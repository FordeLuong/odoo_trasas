# -*- coding: utf-8 -*-
import logging
import uuid
import requests
import base64
import hashlib
import json
import io
import zipfile
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TrasasSignatureProvider(models.Model):
    """
    Nhà cung cấp chữ ký số - Cấu hình kết nối API

    Abstract provider pattern: mỗi provider_type implement
    _{type}_test_connection(), _{type}_send_document(),
    _{type}_get_status(), _{type}_download_signed(), _{type}_cancel()
    """

    _name = "trasas.signature.provider"
    _description = "Nhà cung cấp chữ ký số"
    _order = "sequence, name"

    name = fields.Char(
        string="Tên nhà cung cấp",
        required=True,
        help="Tên hiển thị, VD: VNPT SmartCA",
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
            ("vnpt_smartca", "VNPT SmartCA (ký số từ xa)"),
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
        """Tải tài liệu đã ký. Returns: base64 encoded file."""
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
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url")
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

    # ==================================================================
    # VNPT SMARTCA PROVIDER IMPLEMENTATION (HASH SIGNING)
    # ==================================================================

    def _vnpt_smartca_base_url(self):
        """Return SmartCA gateway base URL."""
        self.ensure_one()
        if self.api_url:
            return self.api_url.rstrip("/")
        if self.test_mode:
            return "https://rmgateway.vnptit.vn/sca/sp769"
        return "https://gwsca.vnpt.vn/sca/sp769"

    def _vnpt_smartca_headers(self):
        return {"Content-Type": "application/json"}

    def _vnpt_smartca_post(self, path, payload, timeout=30):
        self.ensure_one()
        url = f"{self._vnpt_smartca_base_url()}{path}"
        _logger.info("SmartCA POST %s", url)
        resp = requests.post(
            url,
            headers=self._vnpt_smartca_headers(),
            json=payload,
            timeout=timeout,
        )
        if resp.status_code >= 400:
            raise UserError(
                _("SmartCA HTTP %s: %s") % (resp.status_code, resp.text)
            )
        try:
            return resp.json()
        except Exception:
            raise UserError(
                _("SmartCA response is not JSON: %s") % resp.text
            )

    def _vnpt_smartca_test_connection(self):
        """Validate SP credentials are present."""
        self.ensure_one()
        if not self.api_key or not self.api_secret:
            raise UserError(_("Thiếu SP ID / SP Password (API Key/Secret)."))
        return True

    def _vnpt_smartca_send_document(self, request):
        """Create SmartCA signing transaction per signer (hash signing)."""
        self.ensure_one()
        base_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url")
            .rstrip("/")
        )
        callback_url = (
            f"{base_url}/trasas/signature/callback/{request.callback_token}"
        )

        if not request.hash_hex:
            request._prepare_hash_for_signing()

        batch_ref = f"SMARTCA-{uuid.uuid4().hex[:10].upper()}"
        result = {"provider_document_ref": batch_ref, "signers": []}

        for signer in request.signer_ids.sorted("sign_order"):
            if not signer.id_number:
                raise UserError(
                    _(
                        "Thiếu 'Định danh ký (CCCD/MST)' cho người ký: %s"
                    )
                    % (signer.signer_name or signer.id)
                )

            transaction_id = (
                f"{request.name}-{signer.id}-{uuid.uuid4().hex[:6]}"
            )
            doc_id = f"{request.name}:{signer.id}"

            payload = {
                "sp_id": self.api_key,
                "sp_password": self.api_secret,
                "user_id": signer.id_number,
                "transaction_id": transaction_id,
                "callback_url": callback_url,
                "sign_files": [
                    {
                        "doc_id": doc_id,
                        "file_type": "pdf",
                        "sign_type": "hash",
                        "data_to_be_signed": request.hash_hex,
                    }
                ],
            }

            data = self._vnpt_smartca_post("/v1/signatures/sign", payload)

            tran_code = (
                data.get("tran_code")
                or data.get("tranId")
                or data.get("transaction_code")
                or ""
            )
            if not tran_code:
                _logger.warning(
                    "SmartCA sign: missing tran_code. Response=%s", data
                )

            signer.write(
                {
                    "vnpt_transaction_id": transaction_id,
                    "vnpt_tran_code": tran_code,
                    "provider_signer_ref": tran_code or transaction_id,
                    "vnpt_last_status": str(
                        data.get("status_code")
                        or data.get("status")
                        or "PENDING"
                    ),
                }
            )

            result["signers"].append(
                {
                    "signer_id": signer.id,
                    "signing_url": "",
                    "provider_signer_ref": signer.provider_signer_ref,
                }
            )

        return result

    def _vnpt_smartca_get_status(self, request):
        """Poll status per signer using tran_code."""
        self.ensure_one()
        res = {"request_status": "pending", "signers": []}
        all_signed = True
        any_refused = False

        for signer in request.signer_ids:
            tran = signer.vnpt_tran_code or signer.provider_signer_ref
            if not tran:
                all_signed = False
                continue

            data = self._vnpt_smartca_post(
                f"/v1/signatures/sign/{tran}/status",
                {
                    "sp_id": self.api_key,
                    "sp_password": self.api_secret,
                    "user_id": signer.id_number or "",
                },
            )

            status_code = (
                data.get("status_code")
                or data.get("status")
                or data.get("state")
            )
            status_str = (
                str(status_code).lower() if status_code is not None else ""
            )
            signed_files = (
                data.get("signatures") or data.get("signed_files") or []
            )
            sig_val = None
            ts_sig = None
            if signed_files and isinstance(signed_files, list):
                first = signed_files[0] or {}
                sig_val = first.get("signature_value") or first.get(
                    "signature"
                )
                ts_sig = first.get("timestamp_signature") or first.get(
                    "sign_time"
                )

            mapped = "waiting"
            signed_date = False
            if "signed" in status_str or status_str in (
                "1",
                "success",
                "completed",
                "done",
            ):
                mapped = "signed"
                signed_date = fields.Datetime.now()
            elif "refus" in status_str or status_str in (
                "2",
                "rejected",
                "cancelled",
                "canceled",
                "fail",
                "failed",
            ):
                mapped = "refused"

            signer.write(
                {
                    "vnpt_last_status": str(status_code),
                    "vnpt_signature_value": sig_val
                    or signer.vnpt_signature_value,
                    "vnpt_timestamp_signature": ts_sig
                    or signer.vnpt_timestamp_signature,
                }
            )

            if mapped != "signed":
                all_signed = False
            if mapped == "refused":
                any_refused = True

            res["signers"].append(
                {
                    "provider_signer_ref": signer.provider_signer_ref,
                    "status": mapped,
                    "signed_date": signed_date,
                }
            )

        if any_refused:
            res["request_status"] = "cancelled"
        elif all_signed and request.signer_ids:
            res["request_status"] = "completed"
        return res

    def _vnpt_smartca_download_signed(self, request):
        """Return ZIP package (pdf + signatures.json) for hash signing."""
        self.ensure_one()
        pdf_bytes = base64.b64decode(request.document_file or b"")
        audit = {
            "provider": "VNPT SmartCA",
            "provider_type": "vnpt_smartca",
            "request": request.name,
            "contract": (
                request.contract_id.name if request.contract_id else None
            ),
            "hash_algo": request.hash_algo,
            "hash_hex": request.hash_hex,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "signers": [],
        }
        for s in request.signer_ids.sorted("sign_order"):
            audit["signers"].append(
                {
                    "name": s.signer_name,
                    "email": s.signer_email,
                    "role": s.role,
                    "id_number": s.id_number,
                    "serial_number": s.vnpt_serial_number,
                    "tran_code": s.vnpt_tran_code,
                    "transaction_id": s.vnpt_transaction_id,
                    "status": s.state,
                    "signed_date": (
                        s.signed_date.isoformat() if s.signed_date else None
                    ),
                    "signature_value": s.vnpt_signature_value,
                    "timestamp_signature": s.vnpt_timestamp_signature,
                    "last_status": s.vnpt_last_status,
                }
            )

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(
                request.document_filename or "document.pdf", pdf_bytes
            )
            z.writestr(
                "signatures.json",
                json.dumps(audit, ensure_ascii=False, indent=2),
            )

        package_b64 = base64.b64encode(buf.getvalue())
        request.sudo().write(
            {
                "signed_package_info": json.dumps(
                    audit, ensure_ascii=False
                )
            }
        )
        return package_b64

    def _vnpt_smartca_cancel(self, request):
        """SmartCA does not have a cancel API - just return True."""
        return True
