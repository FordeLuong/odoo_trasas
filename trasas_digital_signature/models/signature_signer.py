# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TrasasSignatureSigner(models.Model):
    """Người ký trong yêu cầu ký số"""

    _name = "trasas.signature.signer"
    _description = "Người ký"
    _order = "sign_order, id"

    request_id = fields.Many2one(
        "trasas.signature.request",
        string="Yêu cầu ký",
        required=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Liên hệ",
        help="Chọn liên hệ để tự động điền tên và email",
    )
    role = fields.Selection(
        [
            ("internal", "Nội bộ (TRASAS)"),
            ("external", "Đối tác/Khách hàng"),
        ],
        string="Vai trò",
        required=True,
    )
    sign_order = fields.Integer(
        string="Thứ tự ký",
        required=True,
        default=10,
        help="Số nhỏ ký trước",
    )
    signer_name = fields.Char(string="Tên người ký", required=True)
    signer_email = fields.Char(string="Email", required=True)
    state = fields.Selection(
        [
            ("waiting", "Chờ"),
            ("sent", "Đã gửi"),
            ("signed", "Đã ký"),
            ("refused", "Từ chối"),
        ],
        string="Trạng thái",
        default="waiting",
        required=True,
    )
    signing_url = fields.Char(string="Link ký", readonly=True, copy=False)
    signed_date = fields.Datetime(string="Ngày ký", readonly=True)
    provider_signer_ref = fields.Char(
        string="Mã NCC",
        readonly=True,
        copy=False,
        help="Mã tham chiếu người ký tại nhà cung cấp",
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.signer_name = self.partner_id.name
            self.signer_email = self.partner_id.email
