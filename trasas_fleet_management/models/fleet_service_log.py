# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FleetVehicleLogServices(models.Model):
    _inherit = "fleet.vehicle.log.services"

    description = fields.Char(string="Mô tả công việc", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.odometer_id and rec.description:
                rec.odometer_id.name = rec.description
        return records

    def write(self, vals):
        res = super().write(vals)
        if "description" in vals or "odometer" in vals or "odometer_id" in vals:
            for rec in self:
                if rec.odometer_id and rec.description:
                    rec.odometer_id.name = rec.description
        return res

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
