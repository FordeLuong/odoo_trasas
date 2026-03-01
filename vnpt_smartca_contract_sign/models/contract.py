# -*- coding: utf-8 -*-
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..services.smartca_client import SmartCAClient
from ..services.pades_cms import PadesCms

class VnptContract(models.Model):
    _name = "vnpt.contract"
    _description = "Contract (VNPT SmartCA + Customer Portal)"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]

    name = fields.Char(required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", required=True, tracking=True)

    # PDF nguồn (unsigned)
    unsigned_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Unsigned PDF",
        domain=[("mimetype", "=", "application/pdf")],
        tracking=True,
    )

    # Placeholder (PDF có signature placeholder/ByteRange cho chữ ký Giám đốc)
    director_placeholder_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Director Placeholder PDF",
        readonly=True,
        tracking=True,
    )

    # PDF đã ký bởi giám đốc (VNPT)
    director_signed_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Director Signed PDF",
        readonly=True,
        tracking=True,
    )

    # PDF đã ký đầy đủ (khách ký ngoài rồi upload)
    fully_signed_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Fully Signed PDF",
        readonly=True,
        tracking=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("waiting_director", "Waiting Director Signature"),
            ("waiting_customer", "Waiting Customer Signature"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="draft",
        tracking=True,
    )

    # SmartCA transaction info (director)
    smartca_user_id = fields.Char(string="SmartCA User ID", tracking=True)
    smartca_serial_number = fields.Char(string="Certificate Serial", tracking=True)
    smartca_transaction_id = fields.Char(string="Transaction ID", tracking=True)
    smartca_tran_code = fields.Char(string="Tran Code", tracking=True)
    smartca_doc_id = fields.Char(string="doc_id", tracking=True)
    smartca_transaction_desc = fields.Char(string="transaction_desc", tracking=True)
    smartca_time_stamp = fields.Char(string="time_stamp", tracking=True)

    # CMS base64 (audit)
    smartca_signature_value = fields.Text(string="CMS signature_value (base64)", readonly=True)

    # Signature field name for director signature placeholder
    smartca_sig_field = fields.Char(string="Director signature field", default="DirectorSignature1", tracking=True)

    def _get_pdf_bytes_from_attachment(self, attachment):
        if not attachment:
            return b""
        if getattr(attachment, "raw", None):
            return attachment.raw or b""
        if attachment.datas:
            return base64.b64decode(attachment.datas)
        return b""

    def _get_unsigned_pdf_bytes(self):
        self.ensure_one()
        return self._get_pdf_bytes_from_attachment(self.unsigned_attachment_id)

    def _get_director_placeholder_pdf_bytes(self):
        self.ensure_one()
        return self._get_pdf_bytes_from_attachment(self.director_placeholder_attachment_id)

    def _get_director_signed_pdf_bytes(self):
        self.ensure_one()
        return self._get_pdf_bytes_from_attachment(self.director_signed_attachment_id)

    # -------- Portal URL + Mail --------
    def _get_portal_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        token = self._portal_ensure_token()
        return f"{base_url}/my/contracts/{self.id}?access_token={token}"

    def action_send_to_customer(self):
        """Send portal link email to customer after director has signed."""
        self.ensure_one()
        if self.state != "waiting_customer":
            raise UserError(_("Contract is not in 'waiting_customer' state."))
        if not self.partner_id.email:
            raise UserError(_("Customer email is missing."))
        if not self.director_signed_attachment_id:
            raise UserError(_("Missing Director Signed PDF."))

        template = self.env.ref("vnpt_smartca_contract_full.mail_template_contract_customer_sign", raise_if_not_found=False)
        if not template:
            raise UserError(_("Mail template not found."))

        portal_url = self._get_portal_url()
        ctx = dict(self.env.context, portal_url=portal_url)
        template.with_context(ctx).send_mail(self.id, force_send=True)
        self.message_post(body=_("Sent portal link to customer: %s") % self.partner_id.email)
        return True

    # -------- Actions --------
    def action_request_director_signature(self):
        self.ensure_one()
        if not self.unsigned_attachment_id:
            raise UserError(_("Please attach Unsigned PDF first."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Director Signature (VNPT SmartCA)"),
            "res_model": "vnpt.director.sign.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_contract_id": self.id},
        }

    # -------- Cron: poll SmartCA status and embed director signature --------
    @api.model
    def _cron_poll_smartca_director(self):
        ICP = self.env["ir.config_parameter"].sudo()
        limit = int(ICP.get_param("vnpt_smartca.poll_limit") or 50)

        contracts = self.search(
            [("state", "=", "waiting_director"), ("smartca_transaction_id", "!=", False)],
            limit=limit,
        )
        if not contracts:
            return

        client = SmartCAClient(self.env)
        pades = PadesCms()

        for c in contracts:
            try:
                status = client.sign_status(c.smartca_transaction_id)
                sigs = (status.get("data", {}) or {}).get("signatures", []) or []
                if not sigs:
                    continue

                sig_item = None
                if c.smartca_doc_id:
                    for it in sigs:
                        if it.get("doc_id") == c.smartca_doc_id:
                            sig_item = it
                            break
                sig_item = sig_item or sigs[0]

                cms_b64 = sig_item.get("signature_value")
                if not cms_b64:
                    continue  # still pending

                placeholder_pdf = c._get_director_placeholder_pdf_bytes()
                if not placeholder_pdf:
                    raise UserError(_("Missing director placeholder PDF."))

                signed_pdf = pades.embed_cms_into_placeholder_pdf(
                    placeholder_pdf_bytes=placeholder_pdf,
                    cms_signature_b64=cms_b64,
                    field_name=c.smartca_sig_field or "DirectorSignature1",
                )

                att = self.env["ir.attachment"].create({
                    "name": (c.unsigned_attachment_id.name or c.name) + " (director-signed).pdf",
                    "type": "binary",
                    "mimetype": "application/pdf",
                    "raw": signed_pdf,
                    "res_model": c._name,
                    "res_id": c.id,
                })

                c.write({
                    "director_signed_attachment_id": att.id,
                    "smartca_signature_value": cms_b64,
                    "state": "waiting_customer",
                })
                c.message_post(body=_("Director signed successfully via VNPT SmartCA. Waiting for customer signature."))

            except Exception as e:
                c.write({"state": "failed"})
                c.message_post(body=_("Director signing failed: %s") % (e,))