# -*- coding: utf-8 -*-
from odoo import models, fields


class FleetMaintenanceType(models.Model):
    _name = "fleet.maintenance.type"
    _description = "Loại bảo dưỡng phương tiện"
    _order = "months"

    name = fields.Char(string="Tên gói bảo dưỡng", required=True)
    months = fields.Integer(string="Số tháng (chu kỳ)", required=True, default=6)
    active = fields.Boolean(default=True)


class FleetLegalDocumentType(models.Model):
    _name = "fleet.legal.document.type"
    _description = "Loại hồ sơ pháp lý xe"
    _order = "sequence"

    name = fields.Char(string="Tên loại hồ sơ", required=True)
    code = fields.Char(string="Mã (nếu có)")
    sequence = fields.Integer(default=10)
    is_mandatory = fields.Boolean(
        string="Bắt buộc",
        help="Đánh dấu nếu đây là giấy tờ bắt buộc để xe được hoạt động (Đăng ký, Đăng kiểm...)",
    )
    active = fields.Boolean(default=True)


class FleetIssuingAuthority(models.Model):
    _name = "fleet.issuing.authority"
    _description = "Cơ quan cấp giầy tờ"

    name = fields.Char(string="Tên cơ quan", required=True)
    address = fields.Char(string="Địa chỉ")
    active = fields.Boolean(default=True)
