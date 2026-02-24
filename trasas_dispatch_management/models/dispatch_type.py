from odoo import models, fields


class TrasasDispatchType(models.Model):
    _name = "trasas.dispatch.type"
    _description = "Loại công văn"
    _order = "name"

    name = fields.Char(string="Tên loại", required=True)
    code = fields.Char(string="Mã", help="Mã viết tắt (nếu có)")
    active = fields.Boolean(default=True)
    description = fields.Text(string="Mô tả")
