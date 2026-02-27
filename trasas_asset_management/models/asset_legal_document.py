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

    document_type = fields.Selection(
        [
            # --- NXCT: Nhà cửa / Công trình ---
            ("cn_qsdd", "Chứng nhận QSDĐ & sở hữu nhà"),
            ("gpxd", "Giấy phép xây dựng"),
            ("hd_thue_nha", "HĐ thuê nhà / mặt bằng / kho bãi"),
            ("bb_nghiemthu_ct", "Biên bản nghiệm thu công trình"),
            # --- MMTB: Máy móc thiết bị ---
            ("cn_sohuuts", "Chứng nhận sở hữu tài sản"),
            ("hoadon", "Hóa đơn"),
            ("baohanh_mm", "Giấy tờ bảo hành (Máy móc)"),
            ("hd_thue_tb", "Hợp đồng thuê thiết bị"),
            ("bb_nghiemthu", "Biên bản nghiệm thu"),
            # --- TBVP: Thiết bị văn phòng ---
            ("hoadon_muaban", "Hóa đơn mua bán"),
            ("baohanh_vp", "Giấy tờ bảo hành (Văn phòng)"),
            ("hd_thue_tbvp", "HĐ thuê thiết bị văn phòng"),
            ("baohiem_ts", "Giấy tờ bảo hiểm tài sản"),
            # --- TSVH: Tài sản vô hình ---
            ("cn_shtt", "Giấy chứng nhận sở hữu trí tuệ"),
            ("gp_phanmem", "Giấy phép sử dụng phần mềm"),
            ("hd_chuyen_nhuong_shtt", "HĐ chuyển nhượng quyền SHTT"),
            ("bv_banquyen_pm", "Giấy bảo vệ bản quyền phần mềm"),
            # --- Chung ---
            ("other", "Khác"),
        ],
        string="Loại chứng từ",
        required=True,
        default="other",
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
    issuing_authority = fields.Char(
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

    @api.onchange("document_type")
    def _onchange_document_type(self):
        """Tự điền tên giấy tờ từ loại chứng từ đã chọn"""
        if self.document_type and self.document_type != "other":
            type_label = dict(self._fields["document_type"].selection).get(
                self.document_type, ""
            )
            if not self.name:
                self.name = type_label
