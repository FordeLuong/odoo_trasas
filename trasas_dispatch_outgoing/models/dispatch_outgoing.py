from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TrasasDispatchOutgoing(models.Model):
    _name = "trasas.dispatch.outgoing"
    _description = "Công văn đi"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # --- Thông tin chung ---
    name = fields.Char(
        string="Mã hệ thống",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        tracking=True,
    )
    subject = fields.Char(string="Trích yếu", required=True, tracking=True)

    dispatch_number = fields.Char(
        string="Số công văn đi",
        tracking=True,
        readonly=True,
        help="Số chính thức do HCNS cấp sau khi đóng dấu",
    )

    # --- Ngày tháng ---
    date_created = fields.Date(
        string="Ngày soạn thảo", default=fields.Date.context_today, required=True
    )
    date_promulgated = fields.Date(
        string="Ngày ban hành",
        tracking=True,
        help="Ngày HCNS đóng dấu và cấp số",
        readonly=True,
    )

    # --- Các bên liên quan ---
    drafter_id = fields.Many2one(
        "res.users",
        string="Người soạn",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    department_id = fields.Many2one(
        "hr.department",
        string="Phòng ban",
        compute="_compute_department_id",
        store=True,
        readonly=True,
    )
    recipient_id = fields.Many2one(
        "res.partner",
        string="Nơi gửi đến",
        required=True,
        tracking=True,
        domain="[('is_company', '=', True)]",
        help="Chọn công ty/đối tác từ danh bạ",
    )

    def _default_approver(self):
        """Mặc định chọn người duyệt đầu tiên tìm thấy trong Ban Giám đốc"""
        try:
            # Tìm Department bằng XML ID để đảm bảo chính xác
            dept = self.env.ref(
                "trasas_demo_users.dep_ban_giam_doc", raise_if_not_found=False
            )
            if dept:
                # Tìm nhân viên thuộc phòng này có User liên kết
                employee = self.env["hr.employee"].search(
                    [("department_id", "=", dept.id), ("user_id", "!=", False)], limit=1
                )
                return employee.user_id
        except Exception:
            return False
        return False

    approver_id = fields.Many2one(
        "res.users",
        string="Người duyệt",
        required=True,
        tracking=True,
        default=_default_approver,
        domain="[('employee_ids.department_id.name', '=', 'Ban Giám đốc')]",
    )

    # --- Nội dung & File ---
    draft_file = fields.Binary(string="File dự thảo", attachment=True)
    draft_filename = fields.Char(string="Tên file dự thảo")

    official_file = fields.Binary(string="File chính thức", attachment=True)
    official_filename = fields.Char(string="Tên file chính thức")

    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Tài liệu đính kèm",
        help="Các bản dự thảo, phụ lục, tài liệu tham khảo...",
    )

    content = fields.Html(string="Nội dung trích yếu")

    note = fields.Text(string="Ghi chú")

    # --- Lưu trữ ---
    hard_copy_location = fields.Char(
        string="Nơi lưu bản giấy", help="Vị trí lưu trữ hồ sơ giấy (Tủ/Kệ/File...)"
    )

    # --- Trạng thái ---
    state = fields.Selection(
        [
            ("draft", "Dự thảo"),
            ("waiting_approval", "Chờ duyệt"),
            ("approved", "Đã duyệt"),
            ("to_promulgate", "Chờ ban hành"),
            ("processing", "Đang xử lý"),
            ("released", "Đã phát hành"),
            ("sent", "Đã gửi"),
            ("done", "Hoàn thành"),
            ("cancel", "Đã hủy"),
        ],
        string="Trạng thái",
        default="draft",
        tracking=True,
    )

    @api.depends("drafter_id")
    def _compute_department_id(self):
        for record in self:
            if record.drafter_id and record.drafter_id.employee_ids:
                record.department_id = record.drafter_id.employee_ids[0].department_id
            else:
                record.department_id = False

    # --- Sequence Logic ---
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "trasas.dispatch.outgoing.draft"
                    )
                    or "New"
                )
        return super().create(vals_list)

    # --- Actions ---
    def action_generate_number(self):
        """Cấp số công văn chính thức (Chỉ dành cho HCNS)"""
        for record in self:
            if not record.dispatch_number:
                record.dispatch_number = self.env["ir.sequence"].next_by_code(
                    "trasas.dispatch.outgoing.official"
                )
            # Cập nhật ngày ban hành
            record.date_promulgated = fields.Date.today()
            # Giữ state = processing (HCNS tiếp tục đóng dấu, lưu trữ)
            record.state = "processing"
            record.message_post(
                body="Đã cấp số công văn: %s" % record.dispatch_number,
                subtype_xmlid="mail.mt_comment",
            )

    is_user_approver = fields.Boolean(compute="_compute_is_user_approver")

    def _compute_is_user_approver(self):
        for record in self:
            record.is_user_approver = record.approver_id == self.env.user

    def action_submit(self):
        for record in self:
            if not record.draft_file:
                raise ValidationError(
                    "Vui lòng đính kèm File dự thảo trước khi gửi duyệt!"
                )

            # 1. Gửi email template "Yêu cầu duyệt"
            template = self.env.ref(
                "trasas_dispatch_outgoing.email_template_outgoing_to_approve",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

            # 2. Create activity for approver
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=record.approver_id.id,
                summary="Duyệt công văn đi: %s" % record.subject,
                note="Kính gửi Sếp duyệt công văn này.",
            )
        self.state = "waiting_approval"

    def action_approve(self):
        for record in self:
            # 1. Mark activity as done when approved
            # Filter by approver_id to ensure the correct activity is closed even if Admin clicks
            activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
            record.activity_ids.filtered(
                lambda a: (
                    a.activity_type_id.id == activity_type_id
                    and a.user_id.id == record.approver_id.id
                )
            ).action_feedback(feedback="Đã duyệt")

            # 2. Gửi email template "Đã duyệt"
            template = self.env.ref(
                "trasas_dispatch_outgoing.email_template_outgoing_approved",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

        self.state = "approved"

    def action_reject(self):
        for record in self:
            # 1. Cancel (unlink) activity when rejected
            activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
            record.activity_ids.filtered(
                lambda a: (
                    a.activity_type_id.id == activity_type_id
                    and a.user_id.id == record.approver_id.id
                )
            ).unlink()

            # 2. Gửi email template "Bị từ chối"
            template = self.env.ref(
                "trasas_dispatch_outgoing.email_template_outgoing_rejected",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

        self.state = "draft"

    def action_send_to_hcns(self):
        """Gửi cho bộ phận HCNS để ban hành"""
        for record in self:
            # Tìm Trưởng phòng HCNS bằng XML ID (chính xác nhất)
            hcns_dept = self.env.ref(
                "trasas_demo_users.dep_hcns", raise_if_not_found=False
            )
            # Fallback: tìm bằng tên
            if not hcns_dept:
                hcns_dept = self.env["hr.department"].search(
                    [("name", "ilike", "Hành chính")], limit=1
                )

            hcns_manager = False
            if hcns_dept and hcns_dept.manager_id and hcns_dept.manager_id.user_id:
                hcns_manager = hcns_dept.manager_id.user_id

            if not hcns_manager:
                raise ValidationError(
                    "Không tìm thấy Trưởng phòng HCNS. Vui lòng kiểm tra cấu hình Phòng ban và gán Manager cho phòng HCNS."
                )

            # Tạo Activity cho HCNS (để ban hành)
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=hcns_manager.id,
                summary="Ban hành công văn đi: %s" % record.subject,
                note="Công văn đã được duyệt. Vui lòng cấp số và ban hành.",
            )

        self.state = "to_promulgate"

    # action_promulgate đã bỏ — dùng action_generate_number thay thế

    def action_release(self):
        """HCNS phát hành công văn sau khi đã upload file chính thức"""
        for record in self:
            if not record.official_file:
                raise ValidationError(
                    "Vui lòng tải lên File chính thức trước khi phát hành!"
                )

            # 1. Mark Done Activity "Ban hành" cho user hiện tại (HCNS)
            activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
            record.activity_ids.filtered(
                lambda a: (
                    a.activity_type_id.id == activity_type_id
                    and a.user_id.id == self.env.user.id
                )
            ).action_feedback(feedback="Đã phát hành")

            # 2. Gửi email template "Đã phát hành" cho Người soạn
            template = self.env.ref(
                "trasas_dispatch_outgoing.email_template_outgoing_released",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

            # 3. Tạo Activity cho Người soạn: "Tiếp nhận và gửi cho đối tác"
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=record.drafter_id.id,
                summary="Gửi công văn cho đối tác: %s" % record.subject,
                note="Công văn đã được HCNS cấp số và đóng dấu. Vui lòng tiếp nhận và gửi cho đối tác/khách hàng.",
            )

            record.state = "released"

    def action_send(self):
        """Người soạn gửi công văn đi cho đối tác (B9)"""
        for record in self:
            # Mark Done Activity "Gửi cho đối tác" của Người soạn
            activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
            record.activity_ids.filtered(
                lambda a: (
                    a.activity_type_id.id == activity_type_id
                    and a.user_id.id == record.drafter_id.id
                )
            ).action_feedback(feedback="Đã gửi cho đối tác")

            record.message_post(
                body="Công văn đã được gửi cho đối tác/khách hàng: %s"
                % record.recipient_id.name,
                subtype_xmlid="mail.mt_comment",
            )
        self.state = "sent"

    def action_done(self):
        for record in self:
            record.state = "done"

    def action_cancel(self):
        for record in self:
            record.state = "cancel"

    def action_draft(self):
        for record in self:
            record.state = "draft"
