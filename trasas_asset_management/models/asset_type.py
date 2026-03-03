# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class TrasasAssetType(models.Model):
    """Danh mục nhóm tài sản

    4 nhóm chính theo yêu cầu TRASAS:
    - NXCT: Nhà cửa / Công trình xây dựng / Kho bãi
    - MMTB: Máy móc thiết bị sản xuất
    - TBVP: Thiết bị văn phòng giá trị lớn
    - TSVH: Tài sản vô hình
    """

    _name = "trasas.asset.type"
    _description = "Nhóm tài sản"
    _order = "sequence, name"

    name = fields.Char(
        string="Tên nhóm tài sản",
        required=True,
    )
    code = fields.Char(
        string="Mã viết tắt",
        required=True,
        help="Dùng trong mã tài sản: NXCT, MMTB, TBVP, TSVH",
    )
    group_code = fields.Selection(
        [
            ("nxct", "Nhà cửa / Công trình XD"),
            ("mmtb", "Máy móc thiết bị SX"),
            ("tbvp", "Thiết bị văn phòng"),
            ("tsvh", "Tài sản vô hình"),
        ],
        string="Mã nhóm",
        required=True,
        help="Dùng để ẩn/hiện trường riêng theo nhóm trên form",
    )
    sequence = fields.Integer(string="Thứ tự", default=10)
    sequence_id = fields.Many2one(
        "ir.sequence",
        string="Sequence mã tài sản",
        help="Sequence riêng cho nhóm tài sản này.",
    )
    default_depreciation_rate = fields.Float(
        string="Tỷ lệ khấu hao mặc định (%/năm)",
        default=0.0,
    )
    description = fields.Text(string="Mô tả")
    asset_count = fields.Integer(
        string="Số tài sản",
        compute="_compute_asset_count",
    )
    document_folder_id = fields.Many2one(
        "documents.document",
        string="Folder tài liệu",
        domain="[('type', '=', 'folder')]",
        readonly=True,
    )

    _sql_constraints = [
        ("code_unique", "unique(code)", "Mã viết tắt nhóm tài sản phải là duy nhất!"),
    ]

    @api.depends()
    def _compute_asset_count(self):
        Asset = self.env["trasas.asset"]
        for rec in self:
            rec.asset_count = Asset.search_count([("asset_group_id", "=", rec.id)])

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
            "trasas_asset_management.document_folder_asset_root",
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

    def action_view_assets(self):
        """Smart button: Xem tài sản thuộc nhóm này"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Tài sản — %s") % self.name,
            "res_model": "trasas.asset",
            "view_mode": "list,form",
            "domain": [("asset_group_id", "=", self.id)],
            "context": {"default_asset_group_id": self.id},
        }
