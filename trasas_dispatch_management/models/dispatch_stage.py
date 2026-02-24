from odoo import models, fields


class TrasasDispatchStage(models.Model):
    _name = "trasas.dispatch.stage"
    _description = "Giai đoạn công văn đến"
    _order = "sequence, id"

    name = fields.Char(string="Tên giai đoạn", required=True, translate=True)
    sequence = fields.Integer(string="Thứ tự", default=10)
    fold = fields.Boolean(
        string="Thu gọn trong Kanban",
        default=False,
        help="Giai đoạn này sẽ được thu gọn mặc định trong Kanban view.",
    )
    is_draft = fields.Boolean(
        string="Là giai đoạn Nháp",
        default=False,
        help="Giai đoạn mặc định khi tạo mới công văn.",
    )
    is_done = fields.Boolean(
        string="Là giai đoạn Hoàn thành",
        default=False,
        help="Đánh dấu giai đoạn cuối cùng (Hoàn thành).",
    )
    is_cancel = fields.Boolean(
        string="Là giai đoạn Hủy",
        default=False,
        help="Đánh dấu giai đoạn Hủy.",
    )
    description = fields.Text(string="Mô tả")
    mail_template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        help="Gửi email tự động khi công văn chuyển sang giai đoạn này.",
        domain="[('model', '=', 'trasas.dispatch.incoming')]",
    )
