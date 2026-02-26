# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FleetVehicleLogServices(models.Model):
    _inherit = "fleet.vehicle.log.services"

    def action_start(self):
        """New → Running"""
        for rec in self:
            if rec.state == "new":
                rec.state = "running"

    def action_done(self):
        """Running → Done"""
        for rec in self:
            if rec.state == "running":
                rec.state = "done"

    def action_cancel(self):
        """Any → Cancelled"""
        for rec in self:
            if rec.state in ("new", "running"):
                rec.state = "cancelled"
