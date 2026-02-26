# -*- coding: utf-8 -*-
from odoo import models, fields


class TrasasAssetStage(models.Model):
    """Giai đoạn tài sản - dùng cho Kanban grouping"""

    _name = "trasas.asset.stage"
    _description = "Giai đoạn Tài sản"
    _order = "sequence, id"

    name = fields.Char(
        string="Tên giai đoạn",
        required=True,
        translate=True,
    )

    sequence = fields.Integer(
        string="Thứ tự",
        default=10,
        help="Thứ tự hiển thị trong Kanban",
    )

    fold = fields.Boolean(
        string="Thu gọn trong Kanban",
        help="Nếu chọn, giai đoạn này sẽ được thu gọn mặc định trong Kanban",
    )

    state = fields.Selection(
        [
            ("draft", "Mới"),
            ("in_use", "Đang sử dụng"),
            ("repair", "Sửa chữa"),
            ("maintenance", "Bảo trì định kỳ"),
            ("liquidated", "Thanh lý"),
            ("leased", "Cho thuê"),
            ("lease_in", "Thuê ngoài"),
            ("renovation", "Cải tạo"),
            ("expiring", "Sắp hết hạn"),
            ("contract_ended", "Kết thúc HĐ"),
            ("completed", "Hoàn thành"),
        ],
        string="State liên kết",
        help="State tương ứng, dùng để đồng bộ stage ↔ state khi chuyển trạng thái",
    )

    legend_normal = fields.Char(
        string="Kanban: Bình thường",
        default="Đang xử lý",
        translate=True,
    )
    legend_blocked = fields.Char(
        string="Kanban: Bị chặn",
        default="Bị chặn",
        translate=True,
    )
    legend_done = fields.Char(
        string="Kanban: Hoàn tất",
        default="Sẵn sàng chuyển tiếp",
        translate=True,
    )

    requirements = fields.Text(
        string="Yêu cầu",
        help="Mô tả yêu cầu cần hoàn thành ở giai đoạn này",
    )
