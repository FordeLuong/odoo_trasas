from odoo import models, fields


class TrasasDispatchLocation(models.Model):
    _name = "trasas.dispatch.location"
    _description = "Vị trí lưu trữ công văn"
    _order = "name"

    name = fields.Char(string="Tên vị trí", required=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string="Mô tả")


class TrasasDispatchUrgency(models.Model):
    _name = "trasas.dispatch.urgency"
    _description = "Độ khẩn công văn"
    _order = "sequence, id"

    name = fields.Char(string="Tên độ khẩn", required=True)
    sequence = fields.Integer(default=10)
    color = fields.Integer(string="Màu sắc")
    active = fields.Boolean(default=True)
