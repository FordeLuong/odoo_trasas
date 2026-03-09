# -*- coding: utf-8 -*-
from odoo import models, fields


class ContractRejectReason(models.Model):
    _name = "trasas.contract.reject.reason"
    _description = "Lý do từ chối Hợp đồng"
    _order = "sequence, id"

    name = fields.Char(string="Lý do", required=True, translate=True)
    sequence = fields.Integer(string="Thứ tự", default=10)
    active = fields.Boolean(string="Đang dùng", default=True)


class ContractTag(models.Model):
    _name = "trasas.contract.tag"
    _description = "Thẻ hợp đồng"
    _order = "name"

    name = fields.Char(string="Tên thẻ", required=True, translate=True)
    color = fields.Integer(string="Màu sắc", default=0)
    active = fields.Boolean(string="Đang dùng", default=True)

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Tên thẻ đã tồn tại!"),
    ]
