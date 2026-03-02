# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TrasasAssetContractWizard(models.TransientModel):
    _name = "trasas.asset.contract.wizard"
    _description = "Hop dong"

    asset_id = fields.Many2one(
        "trasas.asset",
        string="Tai san",
        required=True,
    )
    party_a_id = fields.Many2one(
        "res.partner",
        string="Ben A",
        required=True,
    )
    party_b_id = fields.Many2one(
        "res.partner",
        string="Ben B",
        required=True,
    )
    rent_price = fields.Monetary(
        string="Gia thue",
        currency_field="currency_id",
        required=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Tien te",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    sign_date = fields.Date(
        string="Ngay ky",
        default=fields.Date.context_today,
        required=True,
    )
    start_date = fields.Date(
        string="Ngay hieu luc",
        required=True,
    )
    end_date = fields.Date(
        string="Ngay ket thuc hieu luc",
        required=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Hop dong dinh kem",
    )
    note = fields.Text(
        string="Ghi chu",
    )
    action_type = fields.Selection(
        [
            ("lease", "Cho thue"),
            ("lease_direct", "Cho thue (Moi)"),
            ("lease_in", "Thue ngoai"),
        ],
        string="Loai thao tac",
        required=True,
        default="lease",
    )

    @api.model
    def default_get(self, fields_list):
        res = super(TrasasAssetContractWizard, self).default_get(fields_list)
        if (
            self.env.context.get("active_id")
            and self.env.context.get("active_model") == "trasas.asset"
        ):
            res["asset_id"] = self.env.context.get("active_id")
        if self.env.context.get("default_action_type"):
            res["action_type"] = self.env.context.get("default_action_type")
        return res

    def action_confirm_contract(self):
        self.ensure_one()
        asset = self.asset_id

        if self.end_date < self.start_date:
            raise UserError(_("Ngay ket thuc khong duoc nho hon ngay bat dau!"))

        self.env["trasas.asset.contract.history"].create(
            {
                "asset_id": asset.id,
                "party_a_id": self.party_a_id.id,
                "party_b_id": self.party_b_id.id,
                "rent_price": self.rent_price,
                "currency_id": self.currency_id.id,
                "sign_date": self.sign_date,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "attachment_ids": [(6, 0, self.attachment_ids.ids)]
                if self.attachment_ids
                else False,
                "note": self.note,
            }
        )

        # Apply corresponding state transition
        if self.action_type == "lease":
            asset.with_context(skip_contract_wizard=True).action_lease()
        elif self.action_type == "lease_direct":
            asset.with_context(skip_contract_wizard=True).action_lease_direct()
        elif self.action_type == "lease_in":
            asset.with_context(skip_contract_wizard=True).action_lease_in()

        return {"type": "ir.actions.act_window_close"}

