# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ContractType(models.Model):
    """Mẫu hợp đồng - Master Data"""

    _name = "trasas.contract.type"
    _description = "Loại hợp đồng TRASAS"
    _order = "sequence, name"

    name = fields.Char(
        string="Tên loại hợp đồng",
        required=True,
        help="Ví dụ: Hợp đồng mua bán, Hợp đồng dịch vụ, Hợp đồng thuê...",
    )

    code = fields.Char(
        string="Mã", required=True, help="Mã viết tắt, ví dụ: HDMB, HDDV, HDT"
    )

    description = fields.Text(
        string="Mô tả", help="Mô tả chi tiết về loại hợp đồng này"
    )

    sequence = fields.Integer(string="Thứ tự", default=10, help="Thứ tự hiển thị")

    active = fields.Boolean(
        string="Active", default=True, help="Bỏ chọn để ẩn loại hợp đồng này"
    )

    # Quy tắc đặt tên tự động
    name_pattern = fields.Char(
        string="Quy tắc đặt tên",
        help="Ví dụ: {code}/{year}/{sequence:04d} → HDMB/2026/0001",
    )

    # Thời hạn mặc định
    default_duration_days = fields.Integer(
        string="Thời hạn mặc định (ngày)",
        default=365,
        help="Số ngày mặc định cho hợp đồng loại này",
    )

    # Thống kê
    contract_count = fields.Integer(
        string="Số hợp đồng", compute="_compute_contract_count"
    )

    document_folder_id = fields.Many2one(
        "documents.document",
        string="Folder tài liệu",
        domain="[('type', '=', 'folder')]",
        readonly=True,
    )

    @api.depends("code")
    def _compute_contract_count(self):
        """Đếm số hợp đồng theo loại"""
        for record in self:
            record.contract_count = self.env["trasas.contract"].search_count(
                [("contract_type_id", "=", record.id)]
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._create_document_folder()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "name" in vals or "code" in vals:
            for rec in self:
                if rec.document_folder_id:
                    folder_name = f"{rec.code} - {rec.name}" if rec.code else rec.name
                    rec.document_folder_id.sudo().write({"name": folder_name})
        return res

    def _create_document_folder(self):
        root_folder = self.env.ref(
            "trasas_contract_management.document_folder_contract_root",
            raise_if_not_found=False,
        )
        if not root_folder:
            return
        Document = self.env["documents.document"].sudo()
        for rec in self:
            if not rec.document_folder_id:
                folder_name = f"{rec.code} - {rec.name}" if rec.code else rec.name
                folder = Document.create(
                    {
                        "name": folder_name,
                        "type": "folder",
                        "folder_id": root_folder.id,
                    }
                )
                rec.document_folder_id = folder.id

    @api.model
    def _create_folders_for_existing(self):
        records = self.search([("document_folder_id", "=", False)])
        records._create_document_folder()

    def action_view_contracts(self):
        """Xem danh sách hợp đồng thuộc loại này"""
        self.ensure_one()
        return {
            "name": f"Hợp đồng {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "trasas.contract",
            "view_mode": "list,form,kanban",
            "domain": [("contract_type_id", "=", self.id)],
            "context": {"default_contract_type_id": self.id},
        }

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "Mã loại hợp đồng phải là duy nhất!")
    ]
