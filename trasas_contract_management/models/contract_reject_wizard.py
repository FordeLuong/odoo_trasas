# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ContractRejectWizard(models.TransientModel):
    """Wizard để nhập lý do từ chối hợp đồng"""

    _name = "trasas.contract.reject.wizard"
    _description = "Wizard Từ chối Hợp đồng"

    contract_id = fields.Many2one(
        "trasas.contract",
        string="Hợp đồng",
        required=True,
        readonly=True,
    )

    rejection_reason = fields.Text(
        string="Lý do từ chối",
        required=True,
        help="Nhập lý do từ chối hợp đồng",
    )

    def action_confirm_reject(self):
        """Xác nhận từ chối với lý do"""
        self.ensure_one()

        if not self.rejection_reason:
            raise models.ValidationError(_("Vui lòng nhập lý do từ chối!"))

        contract = self.contract_id

        # Cập nhật trạng thái hợp đồng
        contract.write(
            {
                "state": "draft",
                "rejection_reason": self.rejection_reason,
            }
        )

        contract.message_post(
            body=_("[B5] Từ chối - Hợp đồng bị từ chối bởi %s.<br/>Lý do: %s")
            % (self.env.user.name, self.rejection_reason),
            subject=_("Từ chối hợp đồng"),
        )

        # Thông báo cho người tạo
        contract._send_rejected_notification()

        # --- Activity Logic ---
        contract._close_activities()
        contract._schedule_activity(
            contract.user_id.id,
            _("Bị từ chối. Vui lòng kiểm tra và sửa lại: %s") % contract.name,
            deadline=0,
        )

        return {"type": "ir.actions.act_window_close"}
