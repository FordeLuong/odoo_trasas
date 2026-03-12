# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TrasasAssetLegalDocument(models.Model):
    """Giấy tờ pháp lý liên kết với tài sản

    Tuân theo yêu cầu khách hàng:
    STT / Loại chứng từ / Ngày / Cơ quan cấp / Số GCN / Hiệu lực / File / Ghi chú

    Loại chứng từ phân theo nhóm tài sản:
    - NXCT: CN QSDĐ, GPXD, HĐ thuê, Nghiệm thu CT
    - MMTB: CN sở hữu TS, Hóa đơn, Bảo hành, HĐ thuê TB, Nghiệm thu
    - TBVP: Hóa đơn, Bảo hành, HĐ thuê TBVP, Bảo hiểm TS
    - TSVH: CN SHTT, GP phần mềm, HĐ chuyển nhượng SHTT, BV bản quyền PM
    """

    _name = "trasas.asset.legal.document"
    _description = "Giấy tờ pháp lý tài sản"
    _order = "sequence, document_date desc"

    sequence = fields.Integer(string="STT", default=10)

    document_type_id = fields.Many2one(
        "trasas.asset.document.type",
        string="Loại chứng từ",
        required=True,
        help="Chọn loại giấy tờ pháp lý. Danh sách gợi ý theo nhóm tài sản.",
    )
    name = fields.Char(
        string="Tên giấy tờ",
        required=True,
        help="Ví dụ: Giấy chứng nhận QSDĐ, Giấy đăng ký xe, Hợp đồng mua bán...",
    )
    asset_id = fields.Many2one(
        "trasas.asset",
        string="Tài sản",
        required=True,
        ondelete="cascade",
        index=True,
    )
    asset_group_id = fields.Many2one(
        "trasas.asset.type",
        related="asset_id.asset_group_id",
        string="Loại nhóm tài sản",
        store=True,
        help="Dùng để gom nhóm và xuất báo cáo chuẩn tên",
    )
    asset_group = fields.Selection(
        related="asset_id.asset_group",
        string="Nhóm TS",
        store=True,
        help="Dùng để lọc loại chứng từ phù hợp",
    )
    document_date = fields.Date(
        string="Ngày cấp",
        help="Ngày cấp / ngày phát hành giấy tờ",
    )
    issuing_authority_id = fields.Many2one(
        "trasas.asset.authority",
        string="Cơ quan cấp",
        help="Cơ quan phát hành giấy tờ",
    )
    certificate_number = fields.Char(
        string="Số GCN",
        help="Số Giấy Chứng Nhận / Số hiệu văn bản",
    )
    validity_date = fields.Date(
        string="Ngày hết hiệu lực",
        help="Để trống nếu không có thời hạn",
    )
    days_to_expire = fields.Integer(
        string="Số ngày còn lại",
        compute="_compute_days_to_expire",
        store=True,
        help="Số ngày còn lại đến ngày hết hiệu lực",
    )
    detail = fields.Text(
        string="Nội dung chi tiết",
        help="Nội dung chi tiết về giấy tờ pháp lý",
    )
    upload_date = fields.Date(
        string="Ngày upload",
        default=fields.Date.context_today,
        help="Ngày upload tài liệu lên hệ thống",
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "asset_legal_doc_attachment_rel",
        "legal_doc_id",
        "attachment_id",
        string="File đính kèm",
        help="Scan hồ sơ pháp lý",
    )
    note = fields.Text(
        string="Ghi chú",
        help="Nơi lưu bản cứng, VP hay tài sản đang được thế chấp ngân hàng...",
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

    @api.depends("validity_date")
    def _compute_days_to_expire(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.validity_date:
                delta = rec.validity_date - today
                rec.days_to_expire = delta.days
            else:
                rec.days_to_expire = 0

    @api.onchange("document_type_id")
    def _onchange_document_type(self):
        """Tự điền tên giấy tờ từ loại chứng từ đã chọn"""
        if self.document_type_id:
            if not self.name:
                self.name = self.document_type_id.name

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_attachments_to_document()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "attachment_ids" in vals:
            self._sync_attachments_to_document()
        return res

    def _sync_attachments_to_document(self):
        """Tạo documents.document cho mỗi attachment chưa đồng bộ.
        Sử dụng cơ chế copy attachment để tránh vi phạm unique constraint của App Documents.
        """
        Document = self.env["documents.document"].sudo()
        Attachment = self.env["ir.attachment"].sudo()
        for rec in self:
            if not rec.asset_id or not rec.asset_id.document_folder_id or not rec.attachment_ids:
                continue
            
            folder_id = rec.asset_id.document_folder_id.id
            
            # Tìm các attachment đã được sync cho bản ghi này (dựa vào description lưu ID gốc)
            existing_docs = Document.search([
                ('folder_id', '=', folder_id),
                ('res_model', '=', 'trasas.asset.legal.document'),
                ('res_id', '=', rec.id)
            ])
            synced_att_ids = []
            for d in existing_docs:
                if d.attachment_id and d.attachment_id.description:
                    synced_att_ids.append(d.attachment_id.description)

            for attachment in rec.attachment_ids:
                att_key = str(attachment.id)
                if att_key in synced_att_ids:
                    continue
                
                # Tạo bản sao attachment để tách biệt "chủ sở hữu" (Tránh UniqueViolation)
                new_att = Attachment.create({
                    'name': attachment.name,
                    'datas': attachment.datas,
                    'mimetype': attachment.mimetype,
                    'description': att_key, # Lưu lại ID gốc để nhận diện đã sync
                    'res_model': 'trasas.asset.legal.document',
                    'res_id': rec.id,
                })

                Document.create({
                    "name": rec.name or attachment.name,
                    "folder_id": folder_id,
                    "attachment_id": new_att.id,
                    "owner_id": self.env.user.id,
                    "res_model": "trasas.asset",
                    "res_id": rec.asset_id.id,
                })
