# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    contract_reminder_days = fields.Integer(
        string="Số ngày nhắc trước khi hết hạn",
        config_parameter="trasas_contract_management.contract_reminder_days",
        default=30,
        help="Hệ thống sẽ gửi cảnh báo và tạo Activity trước số ngày này.",
    )
