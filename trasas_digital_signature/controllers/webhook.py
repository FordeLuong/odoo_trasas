# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SignatureWebhookController(http.Controller):
    """
    Controller nhận callback từ nhà cung cấp chữ ký số.

    Endpoints:
    - POST /trasas/signature/callback/<token>   (JSON webhook - real providers)
    - GET  /trasas/signature/demo/<token>/<id>  (Demo: mô phỏng ký)
    """

    @http.route(
        "/trasas/signature/callback/<string:token>",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def signature_callback(self, token, **kwargs):
        """Webhook endpoint cho nhà cung cấp chữ ký số."""
        _logger.info("Signature callback received for token: %s", token)

        sig_request = (
            request.env["trasas.signature.request"]
            .sudo()
            .search([("callback_token", "=", token)], limit=1)
        )

        if not sig_request:
            _logger.warning("Signature callback: invalid token %s", token)
            return {"status": "error", "message": "Invalid token"}

        if sig_request.state in ("completed", "cancelled"):
            return {"status": "ok", "message": "Request already finalized"}

        try:
            payload = request.jsonrequest
            sig_request._process_callback(payload)
            return {"status": "ok"}
        except Exception as e:
            _logger.error(
                "Error processing signature callback for %s: %s",
                sig_request.name,
                e,
            )
            return {"status": "error", "message": str(e)}

    @http.route(
        "/trasas/signature/demo/<string:token>/<int:signer_id>",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def signature_demo_sign(self, token, signer_id, **kwargs):
        """
        Demo signing endpoint.
        Mô phỏng người ký click link và hoàn tất ký.
        """
        sig_request = (
            request.env["trasas.signature.request"]
            .sudo()
            .search([("callback_token", "=", token)], limit=1)
        )

        if not sig_request:
            return request.make_response(
                "<html><body>"
                "<h2>Yeu cau ky khong ton tai hoac da het han.</h2>"
                "</body></html>",
                headers=[("Content-Type", "text/html; charset=utf-8")],
            )

        signer = sig_request.signer_ids.filtered(
            lambda s, sid=signer_id: s.id == sid
        )

        if not signer:
            return request.make_response(
                "<html><body>"
                "<h2>Nguoi ky khong hop le.</h2>"
                "</body></html>",
                headers=[("Content-Type", "text/html; charset=utf-8")],
            )

        if signer.state == "signed":
            return request.make_response(
                "<html><body>"
                "<h2>Ban da ky tai lieu nay roi. Cam on!</h2>"
                "</body></html>",
                headers=[("Content-Type", "text/html; charset=utf-8")],
            )

        # Process demo signing
        sig_request._process_callback({"signer_id": signer_id})

        return request.make_response(
            "<html><body>"
            "<h2 style='color: green;'>Ky thanh cong! (Demo)</h2>"
            "<p>Cam on <strong>%s</strong> da ky tai lieu.</p>"
            "<p>Ban co the dong tab nay.</p>"
            "</body></html>" % signer.signer_name,
            headers=[("Content-Type", "text/html; charset=utf-8")],
        )
