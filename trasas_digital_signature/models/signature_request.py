# -*- coding: utf-8 -*-
import logging
import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TrasasSignatureRequest(models.Model):
    """Yêu cầu ký số - liên kết với hợp đồng"""

    _name = "trasas.signature.request"
    _description = "Yêu cầu ký số"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------

    name = fields.Char(
        string="Mã yêu cầu",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        tracking=True,
    )
    contract_id = fields.Many2one(
        "trasas.contract",
        string="Hợp đồng",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    provider_id = fields.Many2one(
        "trasas.signature.provider",
        string="Nhà cung cấp",
        required=True,
        domain=[("active", "=", True)],
        tracking=True,
    )

    # Document
    document_file = fields.Binary(
        string="Tài liệu cần ký",
        required=True,
        attachment=True,
    )
    document_filename = fields.Char(string="Tên file")

    # Signing flow
    signing_flow = fields.Selection(
        [
            ("trasas_first", "TRASAS ký trước"),
            ("partner_first", "Đối tác ký trước"),
        ],
        string="Luồng ký",
        required=True,
        tracking=True,
    )

    # State
    state = fields.Selection(
        [
            ("draft", "Nháp"),
            ("sent", "Đã gửi"),
            ("partially_signed", "Ký một phần"),
            ("completed", "Hoàn tất"),
            ("cancelled", "Đã hủy"),
            ("expired", "Hết hạn"),
        ],
        string="Trạng thái",
        default="draft",
        required=True,
        tracking=True,
    )

    # Signers
    signer_ids = fields.One2many(
        "trasas.signature.signer",
        "request_id",
        string="Người ký",
    )

    # Provider reference
    provider_document_ref = fields.Char(
        string="Mã tham chiếu NCC",
        readonly=True,
        copy=False,
    )

    # Callback
    callback_token = fields.Char(
        string="Token callback",
        readonly=True,
        copy=False,
        index=True,
    )

    # Signed document
    signed_document = fields.Binary(
        string="Tài liệu đã ký",
        attachment=True,
        readonly=True,
    )
    signed_document_filename = fields.Char(string="Tên file đã ký")

    # Dates
    sent_date = fields.Datetime(
        string="Ngày gửi", readonly=True, tracking=True
    )
    completed_date = fields.Datetime(
        string="Ngày hoàn tất", readonly=True, tracking=True
    )
    deadline = fields.Date(string="Hạn ký", tracking=True)

    # People
    user_id = fields.Many2one(
        "res.users",
        string="Người tạo",
        default=lambda self: self.env.user,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Công ty",
        default=lambda self: self.env.company,
    )

    # Computed
    signer_count = fields.Integer(
        string="Số người ký", compute="_compute_signer_stats"
    )
    signed_count = fields.Integer(
        string="Đã ký", compute="_compute_signer_stats"
    )

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------

    @api.depends("signer_ids", "signer_ids.state")
    def _compute_signer_stats(self):
        for record in self:
            signers = record.signer_ids
            record.signer_count = len(signers)
            record.signed_count = len(
                signers.filtered(lambda s: s.state == "signed")
            )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "trasas.signature.request"
                    )
                    or "New"
                )
            if not vals.get("callback_token"):
                vals["callback_token"] = uuid.uuid4().hex
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_send(self):
        """
        Gửi yêu cầu ký đến nhà cung cấp.

        1. Validate
        2. Call provider API
        3. Update signers (signing_url, provider_signer_ref)
        4. Email first signer
        5. Move contract to 'signing' if needed
        """
        self.ensure_one()

        if self.state != "draft":
            raise UserError(
                _("Chỉ có thể gửi yêu cầu ký ở trạng thái Nháp!")
            )
        if not self.document_file:
            raise UserError(_("Vui lòng upload tài liệu cần ký!"))
        if not self.signer_ids:
            raise UserError(_("Vui lòng thêm ít nhất một người ký!"))

        if not self.callback_token:
            self.callback_token = uuid.uuid4().hex

        # Call provider
        result = self.provider_id._provider_send_document(self)

        self.write(
            {
                "provider_document_ref": result.get("provider_document_ref"),
                "state": "sent",
                "sent_date": fields.Datetime.now(),
            }
        )

        # Update signers
        for signer_data in result.get("signers", []):
            signer = self.env["trasas.signature.signer"].browse(
                signer_data["signer_id"]
            )
            if signer.exists():
                signer.write(
                    {
                        "signing_url": signer_data.get("signing_url"),
                        "provider_signer_ref": signer_data.get(
                            "provider_signer_ref"
                        ),
                    }
                )

        # Send to first signer
        self._send_to_next_signer()

        # Transition contract
        contract = self.contract_id
        if contract.state == "approved":
            contract.write({"state": "signing"})
            contract.message_post(
                body=_(
                    "Yêu cầu ký số %s đã được gửi. "
                    "Hợp đồng chuyển sang trạng thái Đang ký."
                )
                % self.name,
            )

        self.message_post(
            body=_("Yêu cầu ký đã được gửi đến nhà cung cấp %s.")
            % self.provider_id.name,
        )
        return True

    def action_cancel(self):
        """Hủy yêu cầu ký"""
        self.ensure_one()
        if self.state in ("completed", "cancelled"):
            raise UserError(
                _("Không thể hủy yêu cầu đã hoàn tất hoặc đã hủy!")
            )

        try:
            self.provider_id._provider_cancel(self)
        except Exception as e:
            _logger.warning("Failed to cancel at provider: %s", e)

        self.write({"state": "cancelled"})
        self.signer_ids.filtered(
            lambda s: s.state in ("waiting", "sent")
        ).write({"state": "waiting"})

        self.message_post(
            body=_("Yêu cầu ký đã bị hủy bởi %s.") % self.env.user.name,
        )

    def action_check_status(self):
        """Kiểm tra trạng thái ký từ nhà cung cấp (manual / cron)"""
        self.ensure_one()
        if self.state not in ("sent", "partially_signed"):
            return
        result = self.provider_id._provider_get_status(self)
        self._process_status_update(result)

    # ------------------------------------------------------------------
    # Internal logic
    # ------------------------------------------------------------------

    def _process_status_update(self, status_data):
        """Process status update from provider (callback or polling)."""
        self.ensure_one()

        for signer_data in status_data.get("signers", []):
            signer = self.signer_ids.filtered(
                lambda s, ref=signer_data[
                    "provider_signer_ref"
                ]: s.provider_signer_ref == ref
            )
            if not signer:
                continue

            new_status = signer_data["status"]
            if new_status == "signed" and signer.state != "signed":
                signer.write(
                    {
                        "state": "signed",
                        "signed_date": signer_data.get("signed_date")
                        or fields.Datetime.now(),
                    }
                )
                self.message_post(
                    body=_("%s đã ký thành công.") % signer.signer_name
                )
                self._send_to_next_signer()

            elif new_status == "refused" and signer.state != "refused":
                signer.write({"state": "refused"})
                self.message_post(
                    body=_("%s đã từ chối ký.") % signer.signer_name
                )

        self._check_completion()

    def _process_callback(self, payload):
        """
        Process webhook callback.
        Demo provider: payload = {'signer_id': int}
        Real providers: call _provider_get_status for truth.
        """
        self.ensure_one()

        if self.provider_id.provider_type == "demo":
            signer_id = payload.get("signer_id")
            if signer_id:
                signer = self.signer_ids.filtered(
                    lambda s, sid=int(signer_id): s.id == sid
                )
                if signer and signer.state != "signed":
                    signer.write(
                        {
                            "state": "signed",
                            "signed_date": fields.Datetime.now(),
                        }
                    )
                    self.message_post(
                        body=_("%s đã ký thành công (Demo).")
                        % signer.signer_name
                    )
                    self._send_to_next_signer()
                    self._check_completion()
        else:
            self.action_check_status()

    def _send_to_next_signer(self):
        """
        Gửi email mời ký cho người ký tiếp theo (theo sign_order).
        Chỉ gửi khi tất cả người ký có order nhỏ hơn đã ký xong.
        """
        self.ensure_one()

        next_signers = self.signer_ids.filtered(
            lambda s: s.state == "waiting"
        ).sorted("sign_order")
        if not next_signers:
            return

        next_signer = next_signers[0]

        # Check prior signers are all signed
        prior_signers = self.signer_ids.filtered(
            lambda s, order=next_signer.sign_order: s.sign_order < order
        )
        if prior_signers and any(
            s.state != "signed" for s in prior_signers
        ):
            return

        next_signer.write({"state": "sent"})
        self._send_signing_invitation(next_signer)

        # Update partial state
        if self.state == "sent":
            has_signed = any(
                s.state == "signed" for s in self.signer_ids
            )
            if has_signed:
                self.write({"state": "partially_signed"})

    def _send_signing_invitation(self, signer):
        """Gửi email mời ký cho một người ký"""
        template = self.env.ref(
            "trasas_digital_signature.email_template_signing_invitation",
            raise_if_not_found=False,
        )
        if template and signer.signer_email:
            template.with_context(
                signer_name=signer.signer_name,
                signer_email=signer.signer_email,
                signing_url=signer.signing_url,
            ).send_mail(self.id, force_send=True)

    def _check_completion(self):
        """Kiểm tra tất cả người ký đã ký → hoàn tất + cập nhật hợp đồng."""
        self.ensure_one()

        all_signed = all(s.state == "signed" for s in self.signer_ids)
        any_refused = any(s.state == "refused" for s in self.signer_ids)

        if any_refused:
            self.write({"state": "cancelled"})
            self.message_post(
                body=_("Yêu cầu ký bị hủy do có người từ chối ký.")
            )
            return

        if all_signed and self.signer_ids:
            # Download signed document
            try:
                signed_doc = self.provider_id._provider_download_signed(self)
                self.write(
                    {
                        "state": "completed",
                        "completed_date": fields.Datetime.now(),
                        "signed_document": signed_doc,
                        "signed_document_filename": (
                            f"signed_{self.document_filename or 'document.pdf'}"
                        ),
                    }
                )
            except Exception as e:
                _logger.error(
                    "Failed to download signed document: %s", e
                )
                self.write(
                    {
                        "state": "completed",
                        "completed_date": fields.Datetime.now(),
                    }
                )

            self.message_post(
                body=_(
                    "Tất cả người ký đã hoàn tất. "
                    "Yêu cầu ký đã hoàn thành!"
                )
            )
            self._update_contract_on_completion()

    def _update_contract_on_completion(self):
        """Cập nhật hợp đồng khi tất cả chữ ký đã thu thập."""
        self.ensure_one()
        contract = self.contract_id

        internal_signer = self.signer_ids.filtered(
            lambda s: s.role == "internal" and s.state == "signed"
        )
        external_signer = self.signer_ids.filtered(
            lambda s: s.role == "external" and s.state == "signed"
        )

        vals = {}
        if internal_signer and not contract.internal_sign_date:
            vals["internal_sign_date"] = internal_signer[0].signed_date
        if external_signer and not contract.partner_sign_date:
            vals["partner_sign_date"] = fields.Date.context_today(self)

        # Attach signed PDF
        if self.signed_document and not contract.final_scan_file:
            vals["final_scan_file"] = self.signed_document
            vals["final_scan_filename"] = (
                self.signed_document_filename
                or f"signed_{contract.name}.pdf"
            )

        if vals:
            contract.write(vals)

        # Complete signing if both parties signed
        if (
            contract.internal_sign_date
            and contract.partner_sign_date
            and contract.final_scan_file
            and contract.state == "signing"
        ):
            contract._complete_signing()

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------

    @api.model
    def _cron_check_signature_status(self):
        """Cron: kiểm tra trạng thái ký định kỳ (fallback cho webhook)."""
        requests = self.search(
            [("state", "in", ("sent", "partially_signed"))]
        )
        for req in requests:
            try:
                req.action_check_status()
            except Exception as e:
                _logger.error(
                    "Error checking signature status for %s: %s",
                    req.name,
                    e,
                )

    @api.model
    def _cron_check_signature_expiry(self):
        """Cron: kiểm tra yêu cầu ký hết hạn."""
        today = fields.Date.context_today(self)
        expired = self.search(
            [
                ("state", "in", ("sent", "partially_signed")),
                ("deadline", "<", today),
            ]
        )
        for req in expired:
            req.write({"state": "expired"})
            req.message_post(body=_("Yêu cầu ký đã hết hạn."))
