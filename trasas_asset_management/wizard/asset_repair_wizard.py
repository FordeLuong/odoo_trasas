# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TrasasAssetRepairWizard(models.TransientModel):
    _name = "trasas.asset.repair.wizard"
    _description = "Thong tin sua chua"

    asset_id = fields.Many2one(
        "trasas.asset",
        string="Tai san",
        required=True,
    )
    name = fields.Char(
        string="Ten hang muc sua chua",
        required=True,
    )
    date = fields.Date(
        string="Ngay phat sinh",
        required=True,
        default=fields.Date.context_today,
    )
    start_date = fields.Date(
        string="Ngay bat dau",
        required=True,
        default=fields.Date.context_today,
    )
    finish_date = fields.Date(
        string="Ngay hoan thanh",
        required=True,
        default=fields.Date.context_today,
    )
    amount = fields.Monetary(
        string="Chi phi",
        required=True,
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
        res = super(TrasasAssetRepairWizard, self).default_get(fields_list)
        if (
            self.env.context.get("active_id")
            and self.env.context.get("active_model") == "trasas.asset"
        ):
            res["asset_id"] = self.env.context.get("active_id")
        return res

    def action_confirm_repair(self):
        self.ensure_one()
        asset = self.asset_id

        if asset.state != "in_use":
            raise UserError(_("Chi tai san Dang su dung moi co the Sua chua!"))

        self.env["trasas.asset.repair.info"].create(
            {
                "asset_id": asset.id,
                "name": self.name,
                "date": self.date,
                "start_date": self.start_date,
                "finish_date": self.finish_date,
                "amount": self.amount,
                "currency_id": self.currency_id.id,
                "note": self.note,
            }
        )

        asset.with_context(skip_repair_wizard=True).action_repair()
        return {"type": "ir.actions.act_window_close"}

