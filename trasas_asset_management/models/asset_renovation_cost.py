# -*- coding: utf-8 -*-
from odoo import models, fields


class TrasasAssetRenovationCost(models.Model):
    _name = "trasas.asset.renovation.cost"
    _description = "Chi phí cải tạo tài sản"
    _order = "date desc, id desc"

    asset_id = fields.Many2one(
        "trasas.asset",
        string="Tài sản",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(
        string="Tên chi phí",
        required=True,
        help="Mô tả ngắn gọn nội dung chi phí cải tạo",
    )
    date = fields.Date(
        string="Ngày phát sinh",
        required=True,
        default=fields.Date.context_today,
    )
    amount = fields.Monetary(
        string="Thành tiền",
        required=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Tiền tệ",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    note = fields.Text(
        string="Ghi chú",
    )
