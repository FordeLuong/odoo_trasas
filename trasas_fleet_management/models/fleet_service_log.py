# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FleetVehicleLogServices(models.Model):
    _inherit = "fleet.vehicle.log.services"

    description = fields.Char(string="Mô tả công việc", tracking=True)
    date_complete = fields.Date(string="Ngày kết thúc")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.odometer_id and rec.description:
                rec.odometer_id.name = rec.description

            # Tự động Tạm ngưng xe nếu tạo mới service ở state = running
            if (
                rec.state == "running"
                and rec.vehicle_id
                and rec.vehicle_id.state != "suspended"
            ):
                rec.vehicle_id.write({"state": "suspended"})

        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if (
                ("description" in vals or "odometer" in vals or "odometer_id" in vals)
                and rec.odometer_id
                and rec.description
            ):
                rec.odometer_id.name = rec.description

            # Bắt sự kiện đổi state thành running (từ statusbar hoặc code)
            if vals.get("state") == "running" and rec.state == "running":
                if rec.vehicle_id and rec.vehicle_id.state != "suspended":
                    rec.vehicle_id.write({"state": "suspended"})

        return res

    def action_start(self):
        """New → Running
        Logic Tạm ngưng xe đã được đưa vào hàm write() để đảm bảo bao quát mọi thao tác.
        """
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
