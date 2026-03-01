# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    smartca_base_url = fields.Char(string="SmartCA Base URL", config_parameter="vnpt_smartca.base_url", default="")
    smartca_sp_id = fields.Char(string="SmartCA SP ID", config_parameter="vnpt_smartca.sp_id")
    smartca_sp_password = fields.Char(string="SmartCA SP Password", config_parameter="vnpt_smartca.sp_password")
    smartca_timeout = fields.Int(string="SmartCA Timeout (s)", config_parameter="vnpt_smartca.timeout", default=30)

    smartca_poll_limit = fields.Int(string="Poll batch size", config_parameter="vnpt_smartca.poll_limit", default=50)