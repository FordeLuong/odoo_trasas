# -*- coding: utf-8 -*-
from odoo import models, fields


class TrasasContractStage(models.Model):
    """Giai đoạn hợp đồng - dùng cho Kanban grouping"""

    _name = "trasas.contract.stage"
    _description = "Giai đoạn Hợp đồng"
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

    legend_normal = fields.Char(
        string="Kanban: Bình thường",
        default="Đang xử lý",
        translate=True,
        help="Tooltip cho trạng thái kanban 'Bình thường'",
    )

    legend_blocked = fields.Char(
        string="Kanban: Bị chặn",
        default="Bị chặn",
        translate=True,
        help="Tooltip cho trạng thái kanban 'Bị chặn'",
    )

    legend_done = fields.Char(
        string="Kanban: Hoàn tất",
        default="Sẵn sàng chuyển tiếp",
        translate=True,
        help="Tooltip cho trạng thái kanban 'Hoàn tất'",
    )

    requirements = fields.Text(
        string="Yêu cầu",
        help="Mô tả yêu cầu cần hoàn thành ở giai đoạn này",
    )
