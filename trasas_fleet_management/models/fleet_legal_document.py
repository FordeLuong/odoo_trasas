# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


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
    synced_document_ids = fields.Many2many(
        "documents.document",
        "fleet_legal_doc_synced_rel",
        "legal_doc_id",
        "document_id",
        string="Synced Documents",
        copy=False,
    )

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
    # CRUD: Sync attachments to Documents module
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_attachments_to_documents()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "attachment_ids" in vals or "vehicle_id" in vals:
            self._sync_attachments_to_documents()
        return res

    def unlink(self):
        # Xóa documents.document đã sync khi xóa legal document
        for rec in self:
            if rec.synced_document_ids:
                rec.synced_document_ids.sudo().unlink()
        return super().unlink()

    def _sync_attachments_to_documents(self):
        """Tạo documents.document cho mỗi attachment chưa đồng bộ,
        đặt vào folder riêng của xe trong Documents."""
        Document = self.env["documents.document"].sudo()
        Attachment = self.env["ir.attachment"].sudo()
        for rec in self:
            if not rec.vehicle_id or not rec.attachment_ids:
                continue

            folder = rec.vehicle_id._get_or_create_document_folder()

            # Thu thập attachment IDs đã sync (qua attachment_id trên document)
            synced_att_ids = set()
            for doc in rec.synced_document_ids:
                if doc.attachment_id:
                    # Lấy original att id từ description
                    synced_att_ids.add(doc.attachment_id.description or "")

            new_docs = Document
            for att in rec.attachment_ids:
                # Dùng att.id làm key để tránh duplicate
                att_key = str(att.id)
                if att_key in synced_att_ids:
                    continue

                # Tạo bản sao attachment (dùng res_model trung lập
                # để tránh documents_fleet bridge tự tạo document)
                att_copy = Attachment.create(
                    {
                        "name": att.name,
                        "datas": att.datas,
                        "mimetype": att.mimetype,
                        "description": att_key,
                        "res_model": "fleet.legal.document",
                        "res_id": rec.id,
                    }
                )

                # Tạo document với attachment_id
                new_doc = Document.create(
                    {
                        "name": rec.name or att.name,
                        "folder_id": folder.id,
                        "attachment_id": att_copy.id,
                        "owner_id": self.env.user.id,
                    }
                )
                # Gắn res_model/res_id để smart button Documents đếm đúng
                new_doc.write(
                    {
                        "res_model": "fleet.vehicle",
                        "res_id": rec.vehicle_id.id,
                    }
                )
                new_docs |= new_doc
                _logger.info(
                    ">>> Created document %s in folder %s for att %s",
                    new_doc.id,
                    folder.id,
                    att.id,
                )

            if new_docs:
                rec.sudo().write(
                    {
                        "synced_document_ids": [(4, doc.id) for doc in new_docs],
                    }
                )
