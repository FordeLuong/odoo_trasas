from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


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
            dept = self.env.ref(
                "trasas_demo_users.dep_ban_giam_doc", raise_if_not_found=False
            )
            if dept:
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

    # --- Stage (Dynamic) ---
    stage_id = fields.Many2one(
        "trasas.dispatch.outgoing.stage",
        string="Giai đoạn",
        tracking=True,
        default=lambda self: self._default_stage_id(),
        group_expand="_read_group_stage_ids",
        index=True,
        copy=False,
    )

    # Computed state from stage flags (backward compatibility)
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
        compute="_compute_state",
        store=True,
        tracking=True,
    )

    is_user_approver = fields.Boolean(compute="_compute_is_user_approver")

    def _default_stage_id(self):
        """Get the default draft stage"""
        return self.env["trasas.dispatch.outgoing.stage"].search(
            [("is_draft", "=", True)], limit=1
        )

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Show all stages in kanban view"""
        return self.env["trasas.dispatch.outgoing.stage"].search([], order="sequence")

    @api.depends(
        "stage_id", "stage_id.is_draft", "stage_id.is_done", "stage_id.is_cancel"
    )
    def _compute_state(self):
        """Derive state from stage for backward compatibility"""
        # Cache stage references
        stage_refs = {
            "outgoing_stage_draft": "draft",
            "outgoing_stage_waiting_approval": "waiting_approval",
            "outgoing_stage_approved": "approved",
            "outgoing_stage_to_promulgate": "to_promulgate",
            "outgoing_stage_processing": "processing",
            "outgoing_stage_released": "released",
            "outgoing_stage_sent": "sent",
            "outgoing_stage_done": "done",
            "outgoing_stage_cancel": "cancel",
        }
        stage_map = {}
        for xmlid, state_val in stage_refs.items():
            stage = self.env.ref(
                f"trasas_dispatch_outgoing.{xmlid}", raise_if_not_found=False
            )
            if stage:
                stage_map[stage.id] = state_val

        for record in self:
            if not record.stage_id:
                record.state = "draft"
            elif record.stage_id.id in stage_map:
                record.state = stage_map[record.stage_id.id]
            elif record.stage_id.is_cancel:
                record.state = "cancel"
            elif record.stage_id.is_done:
                record.state = "done"
            elif record.stage_id.is_draft:
                record.state = "draft"
            else:
                # Custom stages default to processing
                record.state = "processing"

    @api.depends("drafter_id")
    def _compute_department_id(self):
        for record in self:
            if record.drafter_id and record.drafter_id.employee_ids:
                record.department_id = record.drafter_id.employee_ids[0].department_id
            else:
                record.department_id = False

    def _compute_is_user_approver(self):
        for record in self:
            record.is_user_approver = record.approver_id == self.env.user

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

    # --- Helper: get stage by XML ID ---
    def _get_stage(self, xmlid):
        """Get a stage by its XML ID"""
        return self.env.ref(
            f"trasas_dispatch_outgoing.{xmlid}", raise_if_not_found=False
        )

    # --- Actions ---
    def action_generate_number(self):
        """Cấp số công văn chính thức (Chỉ dành cho HCNS)"""
        stage_processing = self._get_stage("outgoing_stage_processing")
        if not stage_processing:
            raise UserError("Chưa cấu hình giai đoạn 'Đang xử lý'!")

        for record in self:
            if not record.dispatch_number:
                record.dispatch_number = self.env["ir.sequence"].next_by_code(
                    "trasas.dispatch.outgoing.official"
                )
            record.date_promulgated = fields.Date.today()
            record.stage_id = stage_processing
            record.message_post(
                body="Đã cấp số công văn: %s" % record.dispatch_number,
                subtype_xmlid="mail.mt_comment",
            )

    def action_submit(self):
        stage_waiting = self._get_stage("outgoing_stage_waiting_approval")
        if not stage_waiting:
            raise UserError("Chưa cấu hình giai đoạn 'Chờ duyệt'!")

        for record in self:
            if not record.draft_file:
                raise ValidationError(
                    "Vui lòng đính kèm File dự thảo trước khi gửi duyệt!"
                )

            # Gửi email template "Yêu cầu duyệt"
            template = stage_waiting.mail_template_id or self.env.ref(
                "trasas_dispatch_outgoing.email_template_outgoing_to_approve",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

            # Create activity for approver
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=record.approver_id.id,
                summary="Duyệt công văn đi: %s" % record.subject,
                note="Kính gửi Sếp duyệt công văn này.",
            )

            record.stage_id = stage_waiting

    def action_approve(self):
        stage_approved = self._get_stage("outgoing_stage_approved")
        if not stage_approved:
            raise UserError("Chưa cấu hình giai đoạn 'Đã duyệt'!")

        for record in self:
            # Mark activity as done
            activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
            record.activity_ids.filtered(
                lambda a: (
                    a.activity_type_id.id == activity_type_id
                    and a.user_id.id == record.approver_id.id
                )
            ).action_feedback(feedback="Đã duyệt")

            # Gửi email template "Đã duyệt"
            template = stage_approved.mail_template_id or self.env.ref(
                "trasas_dispatch_outgoing.email_template_outgoing_approved",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

            record.stage_id = stage_approved

    def action_reject(self):
        """Mở wizard nhập lý do từ chối"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Lý do từ chối",
            "res_model": "trasas.dispatch.outgoing.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_dispatch_id": self.id},
        }

    def action_send_to_hcns(self):
        """Gửi cho bộ phận HCNS để ban hành"""
        stage_to_promulgate = self._get_stage("outgoing_stage_to_promulgate")
        if not stage_to_promulgate:
            raise UserError("Chưa cấu hình giai đoạn 'Chờ ban hành'!")

        for record in self:
            # Tìm Trưởng phòng HCNS
            hcns_dept = self.env.ref(
                "trasas_demo_users.dep_hcns", raise_if_not_found=False
            )
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

            # Tạo Activity cho HCNS
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=hcns_manager.id,
                summary="Ban hành công văn đi: %s" % record.subject,
                note="Công văn đã được duyệt. Vui lòng cấp số và ban hành.",
            )

            record.stage_id = stage_to_promulgate

    def action_release(self):
        """HCNS phát hành công văn sau khi đã upload file chính thức"""
        stage_released = self._get_stage("outgoing_stage_released")
        if not stage_released:
            raise UserError("Chưa cấu hình giai đoạn 'Đã phát hành'!")

        for record in self:
            if not record.official_file:
                raise ValidationError(
                    "Vui lòng tải lên File chính thức trước khi phát hành!"
                )

            # Mark Done Activity cho user hiện tại (HCNS)
            activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
            record.activity_ids.filtered(
                lambda a: (
                    a.activity_type_id.id == activity_type_id
                    and a.user_id.id == self.env.user.id
                )
            ).action_feedback(feedback="Đã phát hành")

            # Gửi email template "Đã phát hành"
            template = stage_released.mail_template_id or self.env.ref(
                "trasas_dispatch_outgoing.email_template_outgoing_released",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

            # Tạo Activity cho Người soạn
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=record.drafter_id.id,
                summary="Gửi công văn cho đối tác: %s" % record.subject,
                note="Công văn đã được HCNS cấp số và đóng dấu. Vui lòng tiếp nhận và gửi cho đối tác/khách hàng.",
            )

            record.stage_id = stage_released

    def action_send(self):
        """Người soạn gửi công văn đi cho đối tác"""
        stage_sent = self._get_stage("outgoing_stage_sent")
        if not stage_sent:
            raise UserError("Chưa cấu hình giai đoạn 'Đã gửi'!")

        for record in self:
            # Mark Done Activity "Gửi cho đối tác"
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

            record.stage_id = stage_sent

    def action_done(self):
        stage_done = self._get_stage("outgoing_stage_done")
        if not stage_done:
            raise UserError("Chưa cấu hình giai đoạn 'Hoàn thành'!")
        for record in self:
            record.stage_id = stage_done

    def action_cancel(self):
        stage_cancel = self._get_stage("outgoing_stage_cancel")
        if not stage_cancel:
            raise UserError("Chưa cấu hình giai đoạn 'Hủy'!")
        for record in self:
            record.stage_id = stage_cancel

    def action_draft(self):
        stage_draft = self._get_stage("outgoing_stage_draft")
        if not stage_draft:
            raise UserError("Chưa cấu hình giai đoạn 'Dự thảo'!")
        for record in self:
            record.stage_id = stage_draft
