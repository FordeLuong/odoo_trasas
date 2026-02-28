# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TrasasAssetReuseWizard(models.TransientModel):
    _name = "trasas.asset.reuse.wizard"
    _description = "Tái sử dụng tài sản"

    asset_id = fields.Many2one(
        "trasas.asset",
        string="Tài sản",
        required=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Khách hàng / Đối tác mới",
        help="Khách hàng thuê mới hoặc Đơn vị cung cấp mới",
    )
    department_id = fields.Many2one(
        "hr.department",
        string="Bộ phận sử dụng mới",
    )
    sign_date = fields.Date(
        string="Ngày ký HĐ",
        default=fields.Date.context_today,
    )
    start_date = fields.Date(
        string="Ngày hiệu lực",
        required=True,
        default=fields.Date.context_today,
    )
    end_date = fields.Date(
        string="Ngày kết thúc",
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
        res = super(TrasasAssetReuseWizard, self).default_get(fields_list)
        if (
            self.env.context.get("active_id")
            and self.env.context.get("active_model") == "trasas.asset"
        ):
            asset = self.env["trasas.asset"].browse(self.env.context.get("active_id"))
            res["asset_id"] = asset.id
            if asset.department_id:
                res["department_id"] = asset.department_id.id
        return res

    def action_confirm_reuse(self):
        self.ensure_one()
        asset = self.asset_id

        if self.end_date < self.start_date:
            raise UserError(_("Ngày kết thúc không được nhỏ hơn ngày bắt đầu!"))

        # 1. Tạo lịch sử hợp đồng mới
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

        # 2. Cập nhật thông tin gốc trên Asset và chuyển về state 'draft'
        update_vals = {
            "state": "draft",
        }

        # Cập nhật Đối tác & Bộ phận nếu có nhập
        if self.partner_id:
            update_vals["supplier_id"] = self.partner_id.id
        if self.department_id:
            update_vals["department_id"] = self.department_id.id

        asset.write(update_vals)

        # 3. Ghi log chatter
        msg = f"Đã **Tái sử dụng** tài sản. Khởi tạo hợp đồng mới từ {self.start_date} đến {self.end_date}. Trạng thái chuyển về **Mới**."
        asset.message_post(body=msg, subject="Tái sử dụng tài sản")
        asset._send_state_change_notification()
