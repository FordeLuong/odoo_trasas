# -*- coding: utf-8 -*-
from odoo import models, fields


class TrasasDocAccessLog(models.Model):
    """Ghi nhận lịch sử truy cập tài liệu (B4 - Audit Trail)"""

    _name = "trasas.doc.access.log"
    _description = "Lịch sử truy cập tài liệu"
    _order = "access_date desc"

    document_id = fields.Many2one(
        "documents.document",
        string="Tài liệu",
        required=True,
        ondelete="cascade",
        index=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Người truy cập",
        required=True,
        index=True,
    )

    action = fields.Selection(
        [
            ("view", "Xem"),
            ("download", "Tải xuống"),
            ("edit", "Chỉnh sửa"),
            ("upload_version", "Upload phiên bản mới"),
            ("access_granted", "Được cấp quyền"),
            ("access_revoked", "Bị thu hồi quyền"),
        ],
        string="Hành động",
        required=True,
    )

    access_date = fields.Datetime(
        string="Thời gian",
        default=fields.Datetime.now,
        readonly=True,
    )

    detail = fields.Text(
        string="Chi tiết",
    )

    ip_address = fields.Char(
        string="Địa chỉ IP",
    )
