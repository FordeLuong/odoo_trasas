# -*- coding: utf-8 -*-
import logging
import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TrasasSignatureProvider(models.Model):
    """
    Nhà cung cấp chữ ký số - Cấu hình kết nối API

    Abstract provider pattern: mỗi provider_type implement
    _{type}_send_document(), _{type}_get_status(),
    _{type}_download_signed(), _{type}_cancel()
    """

    _name = "trasas.signature.provider"
    _description = "Nhà cung cấp chữ ký số"
    _order = "sequence, name"

    name = fields.Char(
        string="Tên nhà cung cấp",
        required=True,
        help="Tên hiển thị, VD: FPT.eSign, VNPT-CA",
    )
    provider_type = fields.Selection(
        selection="_get_provider_types",
        string="Loại nhà cung cấp",
        required=True,
    )
    api_url = fields.Char(
        string="API URL",
        help="Địa chỉ endpoint API của nhà cung cấp",
    )
    api_key = fields.Char(
        string="API Key",
        groups="trasas_contract_management.group_contract_manager",
    )
    api_secret = fields.Char(
        string="API Secret",
        groups="trasas_contract_management.group_contract_manager",
    )
    test_mode = fields.Boolean(
        string="Chế độ test",
        default=True,
        help="Sử dụng môi trường sandbox/test của nhà cung cấp",
    )
    active = fields.Boolean(string="Kích hoạt", default=True)
    sequence = fields.Integer(string="Thứ tự", default=10)
    company_id = fields.Many2one(
        "res.company",
        string="Công ty",
        default=lambda self: self.env.company,
    )
    request_count = fields.Integer(
        string="Số yêu cầu",
        compute="_compute_request_count",
    )

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------

    @api.model
    def _get_provider_types(self):
        """
        Selection values cho provider_type.
        Module mở rộng override method này và gọi super() + append.
        """
        return [
            ("demo", "Demo (Mô phỏng)"),
        ]

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------

    def _compute_request_count(self):
        data = self.env["trasas.signature.request"].read_group(
            [("provider_id", "in", self.ids)],
            ["provider_id"],
            ["provider_id"],
        )
        mapped = {d["provider_id"][0]: d["provider_id_count"] for d in data}
        for record in self:
            record.request_count = mapped.get(record.id, 0)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_view_requests(self):
        """Xem danh sách yêu cầu ký của nhà cung cấp"""
        self.ensure_one()
        return {
            "name": _("Yêu cầu ký - %s") % self.name,
            "type": "ir.actions.act_window",
            "res_model": "trasas.signature.request",
            "view_mode": "list,form",
            "domain": [("provider_id", "=", self.id)],
            "context": {"default_provider_id": self.id},
        }

    def action_test_connection(self):
        """Test kết nối API"""
        self.ensure_one()
        try:
            result = self._provider_test_connection()
            if result:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Thành công"),
                        "message": _("Kết nối thành công với %s!") % self.name,
                        "type": "success",
                        "sticky": False,
                    },
                }
        except Exception as e:
            raise UserError(
                _("Lỗi kết nối với %s:\n%s") % (self.name, str(e))
            )

    # ------------------------------------------------------------------
    # Abstract provider dispatch
    # ------------------------------------------------------------------

    def _call_provider(self, method_suffix, *args, **kwargs):
        """Dispatch to _{provider_type}_{method_suffix}()"""
        self.ensure_one()
        method_name = f"_{self.provider_type}_{method_suffix}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(*args, **kwargs)
        raise UserError(
            _("Nhà cung cấp '%s' chưa implement method '%s'.")
            % (self.provider_type, method_suffix)
        )

    def _provider_test_connection(self):
        return self._call_provider("test_connection")

    def _provider_send_document(self, request):
        """
        Gửi tài liệu đến NCC để ký.

        Returns:
            dict: {
                'provider_document_ref': str,
                'signers': [{
                    'signer_id': int,
                    'signing_url': str,
                    'provider_signer_ref': str,
                }]
            }
        """
        return self._call_provider("send_document", request)

    def _provider_get_status(self, request):
        """
        Kiểm tra trạng thái ký.

        Returns:
            dict: {
                'request_status': 'pending'|'completed'|'cancelled',
                'signers': [{
                    'provider_signer_ref': str,
                    'status': 'waiting'|'signed'|'refused',
                    'signed_date': datetime|False,
                }]
            }
        """
        return self._call_provider("get_status", request)

    def _provider_download_signed(self, request):
        """Tải tài liệu đã ký. Returns: base64 encoded PDF."""
        return self._call_provider("download_signed", request)

    def _provider_cancel(self, request):
        """Hủy yêu cầu ký. Returns: bool."""
        self.ensure_one()
        method_name = f"_{self.provider_type}_cancel"
        if hasattr(self, method_name):
            return getattr(self, method_name)(request)
        _logger.warning(
            "Provider %s does not support cancel. Ignoring.",
            self.provider_type,
        )
        return True

    # ==================================================================
    # DEMO PROVIDER IMPLEMENTATION
    # ==================================================================

    def _demo_test_connection(self):
        return True

    def _demo_send_document(self, request):
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )
        result = {
            "provider_document_ref": f"DEMO-{uuid.uuid4().hex[:8].upper()}",
            "signers": [],
        }
        for signer in request.signer_ids:
            result["signers"].append(
                {
                    "signer_id": signer.id,
                    "signing_url": (
                        f"{base_url}/trasas/signature/demo/"
                        f"{request.callback_token}/{signer.id}"
                    ),
                    "provider_signer_ref": (
                        f"DEMO-SIGNER-{uuid.uuid4().hex[:6].upper()}"
                    ),
                }
            )
        return result

    def _demo_get_status(self, request):
        result = {"request_status": "pending", "signers": []}
        all_signed = True
        for signer in request.signer_ids:
            is_signed = signer.state == "signed"
            if not is_signed:
                all_signed = False
            result["signers"].append(
                {
                    "provider_signer_ref": signer.provider_signer_ref,
                    "status": "signed" if is_signed else "waiting",
                    "signed_date": signer.signed_date,
                }
            )
        if all_signed and request.signer_ids:
            result["request_status"] = "completed"
        return result

    def _demo_download_signed(self, request):
        return request.document_file

    def _demo_cancel(self, request):
        return True
