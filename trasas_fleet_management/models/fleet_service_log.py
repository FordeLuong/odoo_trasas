# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FleetVehicleLogServices(models.Model):
    _inherit = "fleet.vehicle.log.services"

    # Odoo fleet.vehicle.log.services already has 'notes' and 'odometer_id'
    # We ensure they are tracked and possibly add logic if needed.

    @api.onchange("odometer")
    def _onchange_odometer_custom(self):
        # Additional logic when odometer changes during service log entry
        pass
