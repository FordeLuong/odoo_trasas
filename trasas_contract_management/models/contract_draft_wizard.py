# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class TrasasContractDraftWizard(models.TransientModel):
    _name = "trasas.contract.draft.wizard"
    _description = "Wizard Yêu cầu Đặt về nháp"

    contract_id = fields.Many2one(
        "trasas.contract",
        string="Hợp đồng",
        required=True,
        readonly=True,
    )

    reason = fields.Text(
        string="Lý do về nháp",
        required=True,
        help="Nhập lý do tại sao muốn đưa hợp đồng này về nháp (bắt buộc)",
    )

    def action_confirm_draft_request(self):
        self.ensure_one()
        if not self.reason:
            raise UserError(_("Vui lòng nhập lý do đưa về nháp!"))

        # Gọi hàm xử lý bên model contract
        self.contract_id._submit_draft_request(self.reason)

        return {"type": "ir.actions.act_window_close"}
