# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TrasasAssetRenovationWizard(models.TransientModel):
    _name = "trasas.asset.renovation.wizard"
    _description = "Cai tao"

    asset_id = fields.Many2one(
        "trasas.asset",
        string="Tai san",
        required=True,
    )
    name = fields.Char(
        string="Ten hang muc cai tao",
        required=True,
    )
    start_date = fields.Date(
        string="Ngay bat dau",
        required=True,
        default=fields.Date.context_today,
    )
    finish_date = fields.Date(
        string="Ngay ket thuc",
    )
    amount = fields.Monetary(
        string="Chi phi",
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Tien te",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    note = fields.Text(
        string="Ghi chu",
    )

    @api.model
    def default_get(self, fields_list):
        res = super(TrasasAssetRenovationWizard, self).default_get(fields_list)
        if (
            self.env.context.get("active_id")
            and self.env.context.get("active_model") == "trasas.asset"
        ):
            res["asset_id"] = self.env.context.get("active_id")
        return res

    def action_confirm_renovation(self):
        self.ensure_one()
        asset = self.asset_id

        if asset.state != "in_use":
            raise UserError(_("Chi tai san Dang su dung moi co the Cai tao!"))

        vals = {
            "asset_id": asset.id,
            "name": self.name,
            "start_date": self.start_date,
            "date": self.start_date,
            "currency_id": self.currency_id.id,
            "note": self.note,
        }
        if self.finish_date:
            vals["finish_date"] = self.finish_date
        if self.amount:
            vals["amount"] = self.amount

        self.env["trasas.asset.renovation.cost"].create(vals)
        asset.with_context(skip_renovation_wizard=True).action_renovation()
        return {"type": "ir.actions.act_window_close"}
