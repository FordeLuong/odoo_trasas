# -*- coding: utf-8 -*-
from odoo import models, fields


class AssetLocation(models.Model):
    _name = "trasas.asset.location"
    _description = "Vị trí Tài sản"
    _order = "name"

    name = fields.Char(string="Tên vị trí", required=True)
    active = fields.Boolean(default=True)


class AssetAuthority(models.Model):
    _name = "trasas.asset.authority"
    _description = "Cơ quan cấp phát"
    _order = "name"

    name = fields.Char(string="Tên cơ quan", required=True)
    active = fields.Boolean(default=True)


class AssetDocumentType(models.Model):
    _name = "trasas.asset.document.type"
    _description = "Loại giấy tờ tài sản"
    _order = "sequence, name"

    name = fields.Char(string="Tên loại giấy tờ", required=True)
    sequence = fields.Integer(default=10)
    asset_group = fields.Selection(
        [
            ("nxct", "Nhà cửa / Công trình XD"),
            ("mmtb", "Máy móc thiết bị SX"),
            ("tbvp", "Thiết bị văn phòng"),
            ("tsvh", "Tài sản vô hình"),
            ("other", "Khác"),
        ],
        string="Nhóm tài sản áp dụng",
        required=True,
        default="other",
    )
    reminder_days = fields.Integer(
        string="Số ngày nhắc trước",
        default=30,
        help="Số ngày báo trước khi giấy tờ hết hiệu lực.",
    )
    active = fields.Boolean(default=True)
