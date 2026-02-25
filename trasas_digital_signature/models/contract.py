# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TrasasContractDigitalSignature(models.Model):
    """Extension: Thêm chữ ký số API cho Hợp đồng TRASAS"""

    _inherit = "trasas.contract"

    signature_request_ids = fields.One2many(
        "trasas.signature.request",
        "contract_id",
        string="Yêu cầu ký số",
    )
    signature_request_count = fields.Integer(
        string="Số yêu cầu ký số",
        compute="_compute_signature_request_count",
    )

    @api.depends("signature_request_ids")
    def _compute_signature_request_count(self):
        for record in self:
            record.signature_request_count = len(record.signature_request_ids)

    def action_view_signature_requests(self):
        """Mở danh sách yêu cầu ký số"""
        self.ensure_one()
        action = {
            "name": _("Yêu cầu ký số"),
            "type": "ir.actions.act_window",
            "res_model": "trasas.signature.request",
            "view_mode": "list,form",
            "domain": [("contract_id", "=", self.id)],
            "context": {
                "default_contract_id": self.id,
                "default_signing_flow": self.signing_flow,
                "default_deadline": self.sign_deadline,
            },
        }
        if self.signature_request_count == 1:
            action["view_mode"] = "form"
            action["res_id"] = self.signature_request_ids[0].id
        return action

    def action_create_signature_request(self):
        """
        Tạo yêu cầu ký số mới từ hợp đồng.
        Auto-populate signers theo signing_flow.
        """
        self.ensure_one()

        if self.state not in ("approved", "signing"):
            raise UserError(
                _(
                    "Chỉ có thể tạo yêu cầu ký cho hợp đồng "
                    "đã duyệt hoặc đang ký!"
                )
            )

        signer_vals = self._prepare_default_signers()

        return {
            "name": _("Tạo yêu cầu ký số"),
            "type": "ir.actions.act_window",
            "res_model": "trasas.signature.request",
            "view_mode": "form",
            "context": {
                "default_contract_id": self.id,
                "default_signing_flow": self.signing_flow,
                "default_deadline": self.sign_deadline,
                "default_signer_ids": signer_vals,
            },
        }

    def _prepare_default_signers(self):
        """
        Chuẩn bị signer mặc định theo signing_flow.

        trasas_first: TRASAS (order=1) → Đối tác (order=2)
        partner_first: Đối tác (order=1) → TRASAS (order=2)
        """
        self.ensure_one()

        # Internal: approver hoặc user hiện tại
        internal_partner = (
            self.approver_id.partner_id
            if self.approver_id
            else self.env.user.partner_id
        )
        # External: đối tác hợp đồng
        external_partner = self.partner_id

        internal_vals = {
            "partner_id": internal_partner.id,
            "role": "internal",
            "signer_name": internal_partner.name or "",
            "signer_email": internal_partner.email or "",
        }
        external_vals = {
            "partner_id": external_partner.id,
            "role": "external",
            "signer_name": external_partner.name or "",
            "signer_email": external_partner.email or "",
        }

        if self.signing_flow == "trasas_first":
            internal_vals["sign_order"] = 1
            external_vals["sign_order"] = 2
        else:
            external_vals["sign_order"] = 1
            internal_vals["sign_order"] = 2

        return [
            (0, 0, internal_vals),
            (0, 0, external_vals),
        ]
