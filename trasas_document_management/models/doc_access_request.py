# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class TrasasDocAccessRequest(models.Model):
    """Yêu cầu truy cập tài liệu (B7, B8, B9, B10)

    Nhân viên gửi yêu cầu → HCNS duyệt → Hệ thống cấp quyền tạm thời
    → Cron thu hồi khi hết hạn
    """

    _name = "trasas.doc.access.request"
    _description = "Yêu cầu truy cập tài liệu"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Mã yêu cầu",
        readonly=True,
        default="New",
        copy=False,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Người yêu cầu",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Liên hệ",
        related="user_id.partner_id",
        store=True,
    )

    department_id = fields.Many2one(
        "hr.department",
        string="Phòng ban",
        tracking=True,
    )

    is_portal_request = fields.Boolean(
        string="Yêu cầu từ Portal",
        default=False,
        readonly=True,
        help="Đánh dấu yêu cầu được gửi từ cổng Portal bởi người dùng bên ngoài",
    )

    document_ids = fields.Many2many(
        "documents.document",
        string="Tài liệu cần truy cập",
        required=True,
        domain="[('type', '!=', 'folder')]",
    )

    folder_id = fields.Many2one(
        "documents.document",
        string="Thư mục cần truy cập",
        domain="[('type', '=', 'folder')]",
    )

    purpose = fields.Text(
        string="Mục đích truy cập",
        required=True,
        tracking=True,
        help="Ghi rõ lý do cần truy cập tài liệu",
    )

    access_type = fields.Selection(
        [
            ("view", "Chỉ xem"),
            ("edit", "Xem và Chỉnh sửa"),
        ],
        string="Loại quyền",
        default="view",
        required=True,
        tracking=True,
    )

    access_duration = fields.Selection(
        [
            ("1", "1 ngày"),
            ("3", "3 ngày"),
            ("7", "1 tuần"),
            ("30", "1 tháng"),
            ("permanent", "Vĩnh viễn"),
        ],
        string="Thời hạn truy cập",
        default="7",
        required=True,
        tracking=True,
    )

    access_start_date = fields.Datetime(
        string="Bắt đầu truy cập",
        readonly=True,
    )

    access_expiry_date = fields.Datetime(
        string="Hết hạn truy cập",
        readonly=True,
    )

    state = fields.Selection(
        [
            ("draft", "Nháp"),
            ("submitted", "Chờ duyệt"),
            ("approved", "Đã duyệt"),
            ("rejected", "Từ chối"),
            ("expired", "Hết hạn"),
        ],
        string="Trạng thái",
        default="draft",
        tracking=True,
    )

    approved_by = fields.Many2one(
        "res.users",
        string="Người phê duyệt",
        readonly=True,
    )

    reject_reason = fields.Text(
        string="Lý do từ chối",
    )

    # =====================================================================
    # CRUD
    # =====================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("trasas.doc.access.request")
                    or "New"
                )
        return super().create(vals_list)

    # =====================================================================
    # WORKFLOW
    # =====================================================================

    def action_submit(self):
        """Nháp → Chờ duyệt"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Chỉ yêu cầu ở trạng thái Nháp mới được gửi!"))
            rec.write({"state": "submitted"})
            rec.message_post(
                body=_("📤 Yêu cầu truy cập đã được gửi, đang chờ HCNS phê duyệt."),
                subject=_("Gửi yêu cầu truy cập"),
            )
            # Tạo Activity cho HCNS Manager
            manager_group = self.env.ref(
                "trasas_document_management.group_doc_manager",
                raise_if_not_found=False,
            )
            if manager_group:
                for user in manager_group.users:
                    rec.activity_schedule(
                        "mail.mail_activity_data_todo",
                        user_id=user.id,
                        summary=_("Yêu cầu truy cập tài liệu cần phê duyệt: %s")
                        % rec.name,
                        note=_("Nhân viên %s yêu cầu truy cập tài liệu. Mục đích: %s")
                        % (rec.user_id.name, rec.purpose),
                    )

    def action_approve(self):
        """Chờ duyệt → Đã duyệt — Cấp quyền truy cập"""
        for rec in self:
            if rec.state != "submitted":
                raise UserError(_("Chỉ yêu cầu đang Chờ duyệt mới được phê duyệt!"))

            now = fields.Datetime.now()
            expiry = False
            if rec.access_duration != "permanent":
                days = int(rec.access_duration)
                expiry = now + relativedelta(days=days)

            rec.write(
                {
                    "state": "approved",
                    "approved_by": self.env.user.id,
                    "access_start_date": now,
                    "access_expiry_date": expiry,
                }
            )

            # Cấp quyền truy cập trên Documents
            for doc in rec.document_ids:
                self.env["documents.access"].create(
                    {
                        "document_id": doc.id,
                        "partner_id": rec.partner_id.id,
                        "role": rec.access_type,
                        "expiration_date": expiry,
                    }
                )

            # Nếu chọn folder thì cấp quyền trên folder đó
            if rec.folder_id:
                self.env["documents.access"].create(
                    {
                        "document_id": rec.folder_id.id,
                        "partner_id": rec.partner_id.id,
                        "role": rec.access_type,
                        "expiration_date": expiry,
                    }
                )

            # Đóng Activity
            rec.activity_ids.action_done()

            rec.message_post(
                body=_(
                    "✅ Yêu cầu đã được phê duyệt bởi %s. Quyền truy cập đã được cấp%s."
                )
                % (
                    self.env.user.name,
                    _(" đến %s") % expiry.strftime("%d/%m/%Y %H:%M")
                    if expiry
                    else _(" (Vĩnh viễn)"),
                ),
                subject=_("Đã phê duyệt yêu cầu truy cập"),
            )

            # Ghi log
            for doc in rec.document_ids:
                self.env["trasas.doc.access.log"].sudo().create(
                    {
                        "document_id": doc.id,
                        "user_id": rec.user_id.id,
                        "action": "access_granted",
                        "detail": _("Được cấp quyền '%s' qua yêu cầu %s")
                        % (
                            dict(rec._fields["access_type"].selection).get(
                                rec.access_type
                            ),
                            rec.name,
                        ),
                    }
                )

    def action_reject(self):
        """Chờ duyệt → Từ chối"""
        for rec in self:
            if rec.state != "submitted":
                raise UserError(_("Chỉ yêu cầu đang Chờ duyệt mới được từ chối!"))
            rec.write({"state": "rejected"})
            rec.activity_ids.action_done()
            rec.message_post(
                body=_("❌ Yêu cầu đã bị từ chối bởi %s.%s")
                % (
                    self.env.user.name,
                    _(" Lý do: %s") % rec.reject_reason if rec.reject_reason else "",
                ),
                subject=_("Từ chối yêu cầu truy cập"),
            )

    # =====================================================================
    # CRON — Thu hồi quyền tạm thời (B9)
    # =====================================================================

    @api.model
    def _cron_revoke_expired_access(self):
        """Quét các yêu cầu đã duyệt nhưng hết hạn → Đổi state expired"""
        now = fields.Datetime.now()
        expired_requests = self.search(
            [
                ("state", "=", "approved"),
                ("access_expiry_date", "!=", False),
                ("access_expiry_date", "<=", now),
            ]
        )

        for req in expired_requests:
            req.write({"state": "expired"})
            req.message_post(
                body=_("⏰ Quyền truy cập đã hết hạn và tự động thu hồi."),
                subject=_("Hết hạn truy cập"),
            )
