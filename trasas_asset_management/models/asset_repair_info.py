# -*- coding: utf-8 -*-
from odoo import models, fields


class TrasasAssetRepairInfo(models.Model):
    _name = "trasas.asset.repair.info"
    _description = "Thong tin sua chua tai san"
    _order = "date desc, id desc"

    asset_id = fields.Many2one(
        "trasas.asset",
        string="Tai san",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(
        string="Ten hang muc sua chua",
        required=True,
        help="Mo ta ngan gon noi dung sua chua",
    )
    date = fields.Date(
        string="Ngay phat sinh",
        required=True,
        default=fields.Date.context_today,
    )
    start_date = fields.Date(
        string="Ngay bat dau",
        required=True,
        default=fields.Date.context_today,
    )
    finish_date = fields.Date(
        string="Ngay hoan thanh",
        required=True,
        default=fields.Date.context_today,
    )
    amount = fields.Monetary(
        string="Chi phi",
        required=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Tien te",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    note = fields.Text(
        string="Ghi chu",
    )

