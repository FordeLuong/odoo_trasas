from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError


class MessageWizard(models.TransientModel):
    _name = 'message.wizard'
    _description = 'Wizard'

    message = fields.Text('Message', required=True, readonly=True)

    def action_ok(self):
        return {'type': 'ir.actions.act_window_close'}