from odoo import models, fields


class TrasasDispatchOutgoingStage(models.Model):
    _name = "trasas.dispatch.outgoing.stage"
    _description = "Giai đoạn công văn đi"
    _order = "sequence, id"

    name = fields.Char(string="Tên giai đoạn", required=True, translate=True)
    sequence = fields.Integer(string="Thứ tự", default=10)
    fold = fields.Boolean(
        string="Thu gọn trong Kanban",
        default=False,
        help="Giai đoạn này sẽ được thu gọn mặc định trong Kanban view.",
    )
    is_draft = fields.Boolean(string="Là giai đoạn Nháp", default=False)
    is_done = fields.Boolean(string="Là giai đoạn Hoàn thành", default=False)
    is_cancel = fields.Boolean(string="Là giai đoạn Hủy", default=False)
    description = fields.Text(string="Mô tả")
    mail_template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        help="Gửi email tự động khi công văn chuyển sang giai đoạn này.",
        domain="[('model', '=', 'trasas.dispatch.outgoing')]",
    )
