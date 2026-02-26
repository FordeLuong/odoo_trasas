# -*- coding: utf-8 -*-
import logging
import uuid
import base64
import hashlib

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
    hash_algo = fields.Selection(
        [("sha256", "SHA-256"), ("sha1", "SHA-1")],
        string="Thuật toán hash",
        default="sha256",
        tracking=True,
    )
    hash_hex = fields.Char(
        string="Hash HEX",
        readonly=True,
        copy=False,
        help="Giá trị hash (hex) của file cần ký (dùng cho NCC ký hash).",
    )
    signed_package_info = fields.Text(
        string="Thông tin gói ký",
        readonly=True,
        copy=False,
        help="Thông tin kỹ thuật/nhật ký ký số (JSON).",
    )

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

    def _prepare_hash_for_signing(self):
        """Compute hash (hex) for the current document_file."""
        self.ensure_one()
        if not self.document_file:
            return
        raw = base64.b64decode(self.document_file)
        algo = (self.hash_algo or "sha256").lower()
        if algo == "sha1":
            h = hashlib.sha1(raw).hexdigest()
        else:
            h = hashlib.sha256(raw).hexdigest()
        self.hash_hex = h
        return h

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
        5. Chuyển hợp đồng sang 'signing' qua action_start_signing()
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

        # Prepare hash (for hash-sign providers like VNPT SmartCA)
        self._prepare_hash_for_signing()

        # Call provider
        result = self.provider_id._provider_send_document(self)

        self.write(
            {
                "provider_document_ref": result.get("provider_document_ref"),
                "state": "sent",
                "sent_date": fields.Datetime.now(),
            }
        )

        # Update signers with provider data
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

        # Send invitation to first signer
        self._send_to_next_signer()

        # Transition contract: approved → signing
        # Gọi action_start_signing() thay vì ghi trực tiếp state
        # để đảm bảo activities và messages được tạo đúng workflow
        contract = self.contract_id
        if contract.state == "approved":
            contract.action_start_signing()
            _logger.info(
                "Contract %s transitioned to signing via "
                "action_start_signing (digital signature).",
                contract.name,
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
        if not isinstance(result, dict):
            _logger.warning(
                "Provider %s returned invalid status payload for %s: %r",
                self.provider_id.display_name,
                self.display_name,
                result,
            )
            return
        self._process_status_update(result)

    # ------------------------------------------------------------------
    # Internal logic
    # ------------------------------------------------------------------

    def _process_status_update(self, status_data):
        """Process status update from provider (callback or polling)."""
        self.ensure_one()

        for signer_data in status_data.get("signers", []):
            provider_signer_ref = signer_data.get("provider_signer_ref")
            if not provider_signer_ref:
                continue
            signer = self.signer_ids.filtered(
                lambda s, ref=provider_signer_ref: s.provider_signer_ref == ref
            )
            if not signer:
                continue

            new_status = signer_data.get("status")
            if not new_status:
                continue
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
                # Sync: cập nhật hợp đồng ngay khi signer hoàn tất
                self._update_contract_on_signer_signed(signer)
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
                    # Sync: cập nhật hợp đồng ngay khi signer hoàn tất
                    self._update_contract_on_signer_signed(signer)
                    self._send_to_next_signer()
                    self._check_completion()
        else:
            self.action_check_status()

    # ------------------------------------------------------------------
    # Contract synchronization
    # ------------------------------------------------------------------

    def _update_contract_on_signer_signed(self, signer):
        """
        Đồng bộ hợp đồng: cập nhật ngay khi một người ký hoàn tất.

        Maps digital signature roles to contract signing steps:
        - internal signer → contract.internal_sign_date (B11/B15)
        - external signer → contract.partner_sign_date (B13/B14)
        """
        self.ensure_one()
        contract = self.contract_id
        if not contract or contract.state != "signing":
            return

        if signer.role == "internal" and not contract.internal_sign_date:
            contract.write(
                {
                    "internal_sign_date": (
                        signer.signed_date or fields.Datetime.now()
                    ),
                }
            )
            b_code = (
                "B11" if contract.signing_flow == "trasas_first" else "B15"
            )
            contract.message_post(
                body=_(
                    "[%s] TRASAS đã ký số hợp đồng (chữ ký số - %s)"
                ) % (b_code, self.provider_id.name),
            )

        elif signer.role == "external" and not contract.partner_sign_date:
            contract.write(
                {"partner_sign_date": fields.Date.context_today(self)}
            )
            b_code = (
                "B13" if contract.signing_flow == "trasas_first" else "B14"
            )
            contract.message_post(
                body=_(
                    "[%s] Đối tác đã ký số hợp đồng (chữ ký số - %s)"
                ) % (b_code, self.provider_id.name),
            )

    def _finalize_contract(self):
        """
        Hoàn tất đồng bộ hợp đồng khi tất cả chữ ký đã thu thập.

        1. Fallback: đảm bảo internal_sign_date, partner_sign_date đã set
        2. Đính kèm tài liệu đã ký vào contract.final_scan_file
        3. Đóng activities trên hợp đồng
        4. Gọi contract._complete_signing() nếu đủ điều kiện
        """
        self.ensure_one()
        contract = self.contract_id
        if not contract or contract.state != "signing":
            return

        vals = {}

        # Fallback: ensure signing dates are set
        internal_signer = self.signer_ids.filtered(
            lambda s: s.role == "internal" and s.state == "signed"
        )
        external_signer = self.signer_ids.filtered(
            lambda s: s.role == "external" and s.state == "signed"
        )

        if internal_signer and not contract.internal_sign_date:
            vals["internal_sign_date"] = (
                internal_signer[0].signed_date or fields.Datetime.now()
            )
        if external_signer and not contract.partner_sign_date:
            vals["partner_sign_date"] = fields.Date.context_today(self)

        # Attach signed document as final_scan_file
        if self.signed_document and not contract.final_scan_file:
            vals["final_scan_file"] = self.signed_document
            vals["final_scan_filename"] = (
                self.signed_document_filename
                or f"signed_{contract.name}.pdf"
            )

        if vals:
            contract.write(vals)

        # Close pending activities on contract
        try:
            contract._close_activities()
        except Exception:
            _logger.debug(
                "No activities to close on contract %s", contract.name
            )

        # Complete signing if conditions met
        # _complete_signing() requires: state=signing, internal_sign_date,
        # final_scan_file
        if (
            contract.state == "signing"
            and contract.internal_sign_date
            and contract.final_scan_file
        ):
            try:
                contract._complete_signing()
                _logger.info(
                    "Contract %s auto-completed via digital signature.",
                    contract.name,
                )
            except Exception as e:
                _logger.warning(
                    "Cannot auto-complete contract %s: %s. "
                    "Manual completion may be required.",
                    contract.name,
                    e,
                )
                contract.message_post(
                    body=_(
                        "Ký số hoàn tất nhưng chưa thể tự động chuyển "
                        "trạng thái hợp đồng. "
                        "Vui lòng kiểm tra và hoàn tất thủ công."
                    )
                )

    # ------------------------------------------------------------------
    # Signer management
    # ------------------------------------------------------------------

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
        """Kiểm tra tất cả người ký đã ký → hoàn tất + đồng bộ hợp đồng."""
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
            # Download signed document from provider
            try:
                signed_doc = (
                    self.provider_id._provider_download_signed(self)
                )
                fname = self.document_filename or "document.pdf"
                if self.provider_id.provider_type == "vnpt_smartca":
                    signed_fname = (
                        f"signed_{fname.rsplit('.', 1)[0]}.zip"
                    )
                else:
                    signed_fname = f"signed_{fname}"
                self.write(
                    {
                        "state": "completed",
                        "completed_date": fields.Datetime.now(),
                        "signed_document": signed_doc,
                        "signed_document_filename": signed_fname,
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

            # Send completion notification
            self._send_completion_notification()

            # Sync contract: finalize signing flow
            self._finalize_contract()

    def _send_completion_notification(self):
        """Gửi email thông báo hoàn tất ký."""
        template = self.env.ref(
            "trasas_digital_signature.email_template_signing_completed",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

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
