# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FleetLegalDocument(models.Model):
    _name = "fleet.legal.document"
    _description = "Giấy tờ hồ sơ phương tiện"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, document_date desc"

    sequence = fields.Integer(string="STT", default=10)

    document_type = fields.Selection(
        [
            ("registration", "Giấy đăng ký xe"),
            ("inspection", "Phiếu đăng kiểm"),
            ("insurance", "Bảo hiểm xe"),
            ("license_plate", "Giấy tờ biển số"),
            ("ownership", "Chứng nhận sở hữu"),
            ("customs", "Chứng từ hải quan / nhập khẩu"),
            ("repair", "Biên bản sửa chữa / bảo dưỡng"),
            ("accident", "Biên bản tai nạn / xử lý"),
            ("other", "Khác"),
        ],
        string="Loại giấy tờ",
        required=True,
        default="other",
    )

    name = fields.Char(
        string="Tên giấy tờ",
        required=True,
        help="Ví dụ: Giấy đăng ký xe BKS 51F-123.45, Phiếu đăng kiểm kỳ 1/2025...",
    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Phương tiện",
        required=True,
        ondelete="cascade",
        index=True,
    )

    document_date = fields.Date(
        string="Ngày cấp",
        help="Ngày cấp / ngày phát hành giấy tờ",
    )
    issuing_authority = fields.Char(
        string="Cơ quan cấp",
        help="Cơ quan phát hành giấy tờ",
    )
    certificate_number = fields.Char(
        string="Số GCN / Số hiệu",
        help="Số Giấy Chứng Nhận / Số hiệu văn bản",
    )
    validity_date = fields.Date(
        string="Ngày hết hiệu lực",
        help="Để trống nếu không có thời hạn",
    )
    upload_date = fields.Datetime(
        string="Thời gian upload",
        default=fields.Datetime.now,
        readonly=True,
        help="Thời gian tạo bản ghi hồ sơ",
    )
    days_to_expire = fields.Integer(
        string="Số ngày còn lại",
        compute="_compute_days_to_expire",
        store=True,
        help="Số ngày còn lại đến ngày hết hiệu lực",
    )
    state = fields.Selection(
        [
            ("active", "Hiệu lực"),
            ("expiring_soon", "Sắp hết hạn"),
            ("expired", "Hết hiệu lực"),
            ("revoked", "Đã thu hồi"),
        ],
        string="Trạng thái",
        default="active",
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "fleet_legal_doc_attachment_rel",
        "legal_doc_id",
        "attachment_id",
        string="File đính kèm",
        help="Scan / ảnh chụp giấy tờ",
    )
    note = fields.Text(
        string="Ghi chú",
        help="Nơi lưu bản cứng, thông tin thế chấp...",
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.depends("validity_date")
    def _compute_days_to_expire(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.validity_date:
                rec.days_to_expire = (rec.validity_date - today).days
            else:
                rec.days_to_expire = 0

    @api.onchange("document_type")
    def _onchange_document_type(self):
        """Tự điền tên giấy tờ từ loại chứng từ đã chọn"""
        if self.document_type and self.document_type != "other":
            type_label = dict(self._fields["document_type"].selection).get(
                self.document_type, ""
            )
            if not self.name:
                self.name = type_label

    # -------------------------------------------------------------------------
    # CRUD: Sync attachments to vehicle for Documents smart button
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_attachments_to_vehicle()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "attachment_ids" in vals or "vehicle_id" in vals:
            self._sync_attachments_to_vehicle()
        return res

    def _sync_attachments_to_vehicle(self):
        """Cập nhật res_model/res_id của attachment để trỏ về fleet.vehicle,
        giúp hiển thị trong nút Documents trên form xe."""
        for rec in self:
            if rec.vehicle_id and rec.attachment_ids:
                rec.attachment_ids.sudo().write(
                    {
                        "res_model": "fleet.vehicle",
                        "res_id": rec.vehicle_id.id,
                    }
                )
