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
    id_number = fields.Char(
        string="Định danh ký (CCCD/MST)",
        help="Định danh thuê bao chữ ký số tại NCC (VD: CCCD/CMND/Hộ chiếu/MST).",
    )
    vnpt_serial_number = fields.Char(string="Serial chứng thư", readonly=True, copy=False)
    vnpt_tran_code = fields.Char(string="Mã giao dịch (tran_code)", readonly=True, copy=False)
    vnpt_transaction_id = fields.Char(string="Transaction ID", readonly=True, copy=False)
    vnpt_signature_value = fields.Text(string="Giá trị chữ ký (signature_value)", readonly=True, copy=False)
    vnpt_timestamp_signature = fields.Char(string="Timestamp chữ ký", readonly=True, copy=False)
    vnpt_last_status = fields.Char(string="Trạng thái SmartCA", readonly=True, copy=False)

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
