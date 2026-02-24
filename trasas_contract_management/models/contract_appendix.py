# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class TrasasContractAppendix(models.Model):
    """Model quản lý Phụ lục Hợp đồng"""

    _name = "trasas.contract.appendix"
    _description = "Phụ lục Hợp đồng"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sign_date desc, create_date desc"

    name = fields.Char(string="Số/Tên phụ lục", required=True, tracking=True)
    contract_id = fields.Many2one(
        "trasas.contract",
        string="Hợp đồng gốc",
        required=True,
        ondelete="cascade",
        tracking=True,
    )

    content = fields.Html(string="Nội dung", help="Nội dung chi tiết của phụ lục")

    sign_date = fields.Date(
        string="Ngày ký",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    scan_file = fields.Binary(string="File Scan", attachment=True)
    scan_filename = fields.Char(string="Tên file scan")

    state = fields.Selection(
        [
            ("draft", "Nháp"),
            ("signed", "Đã ký"),
        ],
        string="Trạng thái",
        default="draft",
        tracking=True,
    )

    def action_confirm_signed(self):
        """Xác nhận đã ký phụ lục"""
        for record in self:
            record.state = "signed"

    def action_set_to_draft(self):
        """Đặt lại về nháp"""
        for record in self:
            record.state = "draft"
