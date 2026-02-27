# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import timedelta


class DocumentsDocumentInherit(models.Model):
    """Kế thừa documents.document — Bổ sung trường thông tin cơ bản (B2b),
    trạng thái hiệu lực, và cảnh báo hết hạn (B5, B12)
    """

    _inherit = "documents.document"

    # =====================================================================
    # THÔNG TIN CƠ BẢN BỔ SUNG (B2b)
    # =====================================================================

    document_type = fields.Selection(
        [
            ("contract", "Hợp đồng"),
            ("license", "Giấy phép"),
            ("appendix", "Phụ lục"),
            ("regulation", "Nội quy / Quy định"),
            ("policy", "Chính sách"),
            ("certificate", "Chứng chỉ / Chứng nhận"),
            ("report", "Báo cáo"),
            ("other", "Khác"),
        ],
        string="Loại hồ sơ",
        tracking=True,
        help="Phân loại loại hình tài liệu",
    )

    document_number = fields.Char(
        string="Số hiệu văn bản",
        tracking=True,
    )

    issuing_authority = fields.Char(
        string="Cơ quan cấp / Ban hành",
        tracking=True,
    )

    issue_date = fields.Date(
        string="Ngày cấp / Ban hành",
        tracking=True,
    )

    validity_date = fields.Date(
        string="Ngày hết hiệu lực",
        tracking=True,
        help="Để trống nếu không có thời hạn",
    )

    days_to_expire = fields.Integer(
        string="Số ngày còn lại",
        compute="_compute_days_to_expire",
        store=True,
    )

    confidential_level = fields.Selection(
        [
            ("public", "Công khai"),
            ("internal", "Nội bộ"),
            ("confidential", "Mật"),
            ("restricted", "Tuyệt mật"),
        ],
        string="Độ mật",
        default="internal",
        tracking=True,
    )

    doc_state = fields.Selection(
        [
            ("active", "Hiệu lực"),
            ("expiring_soon", "Sắp hết hạn"),
            ("expired", "Hết hiệu lực"),
            ("revoked", "Đã thu hồi"),
        ],
        string="Trạng thái hiệu lực",
        default="active",
        tracking=True,
    )

    department_id = fields.Many2one(
        "hr.department",
        string="Phòng ban quản lý",
        tracking=True,
    )

    responsible_user_id = fields.Many2one(
        "res.users",
        string="Người phụ trách",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # =====================================================================
    # COMPUTED
    # =====================================================================

    @api.depends("validity_date")
    def _compute_days_to_expire(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.validity_date:
                delta = rec.validity_date - today
                rec.days_to_expire = delta.days
            else:
                rec.days_to_expire = 0

    # =====================================================================
    # CRON — Cảnh báo hết hạn (B5) & Đóng VB hết hiệu lực (B12)
    # =====================================================================

    @api.model
    def _cron_document_expiry_check(self):
        """Quét tài liệu hàng ngày:
        - Trước 30 ngày: Cảnh báo qua Activity
        - Đến hạn: Đổi state → expired + thông báo phòng ban
        - Trước 30 ngày: Đổi state → expiring_soon
        """
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=30)

        # 1. Tìm các VB sắp hết hạn (trong 30 ngày tới) + chưa được cảnh báo
        expiring_docs = self.search(
            [
                ("type", "!=", "folder"),
                ("doc_state", "=", "active"),
                ("validity_date", "!=", False),
                ("validity_date", "<=", warning_date),
                ("validity_date", ">", today),
            ]
        )

        for doc in expiring_docs:
            doc.write({"doc_state": "expiring_soon"})
            if doc.responsible_user_id:
                doc.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=doc.responsible_user_id.id,
                    note=_(
                        "Tài liệu '%s' (Số: %s) sẽ hết hiệu lực vào ngày %s. "
                        "Vui lòng xem xét gia hạn hoặc cập nhật."
                    )
                    % (
                        doc.name,
                        doc.document_number or "N/A",
                        doc.validity_date.strftime("%d/%m/%Y"),
                    ),
                    summary=_("Tài liệu sắp hết hiệu lực: %s") % doc.name,
                )

        # 2. Tìm các VB đã hết hạn → đóng
        expired_docs = self.search(
            [
                ("type", "!=", "folder"),
                ("doc_state", "in", ("active", "expiring_soon")),
                ("validity_date", "!=", False),
                ("validity_date", "<=", today),
            ]
        )

        for doc in expired_docs:
            doc.write({"doc_state": "expired"})
            doc.message_post(
                body=_(
                    "📛 Tài liệu đã hết hiệu lực từ ngày %s. Đã tự động chuyển trạng thái."
                )
                % doc.validity_date.strftime("%d/%m/%Y"),
                subject=_("Tài liệu hết hiệu lực"),
                partner_ids=doc.department_id.member_ids.mapped(
                    "user_id.partner_id"
                ).ids
                if doc.department_id
                else [],
            )

    # =====================================================================
    # THU HỒI VĂN BẢN (B12)
    # =====================================================================

    def action_revoke_document(self):
        """Thu hồi văn bản — gửi thông báo tới phòng ban liên quan"""
        for rec in self:
            rec.write({"doc_state": "revoked"})
            partner_ids = []
            if rec.department_id:
                partner_ids = rec.department_id.member_ids.mapped(
                    "user_id.partner_id"
                ).ids
            rec.message_post(
                body=_(
                    "🔒 Tài liệu '%s' đã bị thu hồi. Vui lòng không sử dụng phiên bản này."
                )
                % rec.name,
                subject=_("Thu hồi văn bản: %s") % rec.name,
                partner_ids=partner_ids,
            )

    def action_reactivate_document(self):
        """Kích hoạt lại tài liệu đã thu hồi"""
        for rec in self:
            rec.write({"doc_state": "active"})
            rec.message_post(
                body=_("✅ Tài liệu '%s' đã được kích hoạt lại.") % rec.name,
                subject=_("Kích hoạt lại tài liệu"),
            )
