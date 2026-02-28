# -*- coding: utf-8 -*-
import json

from odoo import fields, models


class TrasasSignatureApiLog(models.Model):
    _name = "trasas.signature.api.log"
    _description = "Digital Signature API Log"
    _order = "create_date desc, id desc"

    provider_id = fields.Many2one(
        "trasas.signature.provider",
        string="Nhà cung cấp",
        required=True,
        ondelete="cascade",
    )
    provider_type = fields.Selection(
        related="provider_id.provider_type",
        string="Loại NCC",
        store=True,
        readonly=True,
    )
    request_id = fields.Many2one(
        "trasas.signature.request",
        string="Yêu cầu ký",
        ondelete="set null",
    )
    signer_id = fields.Many2one(
        "trasas.signature.signer",
        string="Người ký",
        ondelete="set null",
    )
    operation = fields.Char(string="Thao tác")
    method = fields.Char(string="Method", default="POST")
    endpoint = fields.Char(string="Endpoint")
    url = fields.Char(string="URL")
    status_code = fields.Integer(string="HTTP Code")
    success = fields.Boolean(string="Thành công", default=False)
    duration_ms = fields.Integer(string="Thời gian (ms)")
    request_payload = fields.Text(string="Request Payload")
    response_payload = fields.Text(string="Response Payload")
    error_message = fields.Text(string="Lỗi")
    company_id = fields.Many2one(
        "res.company",
        string="Công ty",
        default=lambda self: self.env.company,
    )

    def _set_request_payload(self, payload):
        self.ensure_one()
        if isinstance(payload, (dict, list)):
            self.request_payload = json.dumps(
                payload, ensure_ascii=False, indent=2
            )
        else:
            self.request_payload = str(payload or "")
