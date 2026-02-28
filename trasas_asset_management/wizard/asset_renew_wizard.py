# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TrasasAssetRenewWizard(models.TransientModel):
    _name = "trasas.asset.renew.wizard"
    _description = "Tái ký Hợp đồng"

    asset_id = fields.Many2one(
        "trasas.asset",
        string="Tài sản",
        required=True,
    )
    sign_date = fields.Date(
        string="Ngày ký",
        default=fields.Date.context_today,
    )
    start_date = fields.Date(
        string="Ngày hiệu lực mới",
        required=True,
    )
    end_date = fields.Date(
        string="Ngày kết thúc mới",
        required=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Hợp đồng đính kèm",
    )
    note = fields.Text(
        string="Ghi chú",
    )

    @api.model
    def default_get(self, fields_list):
        res = super(TrasasAssetRenewWizard, self).default_get(fields_list)
        if (
            self.env.context.get("active_id")
            and self.env.context.get("active_model") == "trasas.asset"
        ):
            res["asset_id"] = self.env.context.get("active_id")
        return res

    def action_confirm_renew(self):
        self.ensure_one()
        asset = self.asset_id

        if self.end_date < self.start_date:
            raise UserError(_("Ngày kết thúc không được nhỏ hơn ngày bắt đầu!"))

        # Tạo lịch sử hợp đồng
        self.env["trasas.asset.contract.history"].create(
            {
                "asset_id": asset.id,
                "sign_date": self.sign_date,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "attachment_ids": [(6, 0, self.attachment_ids.ids)]
                if self.attachment_ids
                else False,
                "note": self.note,
            }
        )

        # Cập nhật thông tin gốc (tùy chọn)
        # Nếu muốn cập nhật vào asset.py luôn thì có thể thêm các field tương ứng.
        # Nhưng quan trọng nhất là cập nhật state
        asset.state = "leased"

        # Thêm log note
        msg = f"Đã tái ký hợp đồng. Hiệu lực từ {self.start_date} đến {self.end_date}."
        asset.message_post(body=msg)
