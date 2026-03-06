# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class TrasasContractCancelWizard(models.TransientModel):
    """Wizard nhập lý do hủy hợp đồng"""

    _name = "trasas.contract.cancel.wizard"
    _description = "Wizard Yêu cầu hủy Hợp đồng"

    contract_id = fields.Many2one(
        "trasas.contract",
        string="Hợp đồng",
        required=True,
        readonly=True,
    )
    cancel_reason = fields.Text(
        string="Lý do hủy",
        required=True,
        help="Vui lòng nhập lý do hủy hợp đồng. Yêu cầu sẽ được gửi cho Trưởng phòng và Ban Giám đốc phê duyệt.",
    )

    def action_confirm_cancel_request(self):
        """Xác nhận gửi yêu cầu hủy"""
        self.ensure_one()
        if not self.cancel_reason:
            raise UserError(_("Vui lòng nhập lý do hủy hợp đồng!"))

        self.contract_id._submit_cancel_request(self.cancel_reason)
        return {"type": "ir.actions.act_window_close"}
