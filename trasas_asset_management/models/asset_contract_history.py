# -*- coding: utf-8 -*-
from odoo import models, fields


class TrasasAssetContractHistory(models.Model):
    _name = "trasas.asset.contract.history"
    _description = "Lịch sử hợp đồng tài sản"
    _order = "sign_date desc, id desc"

    asset_id = fields.Many2one(
        "trasas.asset",
        string="Tài sản",
        required=True,
        ondelete="cascade",
    )
    sign_date = fields.Date(
        string="Ngày ký",
    )
    party_a_id = fields.Many2one(
        "res.partner",
        string="Bên A",
    )
    party_b_id = fields.Many2one(
        "res.partner",
        string="Bên B",
    )
    rent_price = fields.Monetary(
        string="Giá thuê",
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Tiền tệ",
        default=lambda self: self.env.company.currency_id,
    )
    start_date = fields.Date(
        string="Ngày hiệu lực",
        required=True,
    )
    end_date = fields.Date(
        string="Ngày kết thúc",
        required=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="File hợp đồng",
    )
    note = fields.Text(
        string="Ghi chú",
    )
