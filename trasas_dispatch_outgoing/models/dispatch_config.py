from odoo import models, fields


class TrasasDispatchOutgoingRejectReason(models.Model):
    _name = "trasas.dispatch.outgoing.reject.reason"
    _description = "Lý do từ chối công văn"
    _order = "name"

    name = fields.Char(string="Lý do", required=True)
    active = fields.Boolean(default=True)
