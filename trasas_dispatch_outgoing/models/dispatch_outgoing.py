from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class TrasasDispatchOutgoing(models.Model):
    _name = "trasas.dispatch.outgoing"
    _description = "Công văn đi"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # --- Thông tin chung ---
    name = fields.Char(
        string="Số công văn đi",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        tracking=True,
    )
    subject = fields.Char(string="Trích yếu", required=True, tracking=True)

    is_manual_number = fields.Boolean(string="Cấp số thủ công", tracking=True)
    manual_number = fields.Char(string="Số CV (Thủ công)", tracking=True)

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

    incoming_dispatch_id = fields.Many2one(
        "trasas.dispatch.incoming",
        string="Công văn đến gốc",
        readonly=True,
        tracking=True,
        help="Công văn đến mà công văn đi này phản hồi (tự động gắn khi tạo từ CV đến)",
    )

    def _default_approver(self):
        """Mặc định chọn người đầu tiên trong nhóm Ban Giám đốc"""
        group_approver = self.env.ref("trasas_dispatch_management.group_dispatch_approver", raise_if_not_found=False)
        if group_approver:
            # Tìm trực tiếp qua res.users và field group_ids (Odoo 19 environment)
            approver = self.env["res.users"].search([("group_ids", "in", [group_approver.id])], limit=1)
            return approver
        return False

    approver_id = fields.Many2one(
        "res.users",
        string="Người duyệt",
        required=True,
        tracking=True,
        default=_default_approver,
        domain=lambda self: [
            (
                "group_ids",
                "in",
                [self.env.ref("trasas_dispatch_management.group_dispatch_approver").id],
            ),
        ],
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
    location_id = fields.Many2one(
        "trasas.dispatch.location",
        string="Nơi lưu bản giấy",
        help="Vị trí lưu trữ hồ sơ giấy (Tủ/Kệ/File...)",
        tracking=True,
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
                # Custom stages default to draft if no match
                record.state = "draft"

    @api.depends("drafter_id")
    def _compute_department_id(self):
        for record in self:
            if record.drafter_id and record.drafter_id.employee_ids:
                record.department_id = record.drafter_id.employee_ids[0].department_id
            else:
                record.department_id = False

    def _compute_is_user_approver(self):
        is_approver_grp = self.env.user.has_group(
            "trasas_dispatch_management.group_dispatch_approver"
        )
        is_reviewer_grp = self.env.user.has_group(
            "trasas_dispatch_management.group_dispatch_reviewer"
        )
        is_dispatch_admin = self.env.user.has_group(
            "trasas_dispatch_management.group_dispatch_administrator"
        )
        is_admin = self.env.user.has_group("base.group_system")

        for record in self:
            # Người được gán trực tiếp HOẶC (người thuộc nhóm duyệt/admin)
            is_assigned = record.approver_id == self.env.user
            record.is_user_approver = (
                is_assigned or is_admin or is_dispatch_admin or is_approver_grp or is_reviewer_grp
            )

    @api.constrains("is_manual_number", "manual_number")
    def _check_manual_number_unique(self):
        for record in self:
            if record.is_manual_number and record.manual_number:
                domain = [
                    ("is_manual_number", "=", True),
                    ("manual_number", "=", record.manual_number),
                    ("id", "!=", record.id),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        f"Số công văn thủ công '{record.manual_number}' đã tồn tại!"
                    )

    @api.onchange("is_manual_number", "manual_number")
    def _onchange_manual_number(self):
        if self.is_manual_number and self.manual_number:
            domain = [
                ("is_manual_number", "=", True),
                ("manual_number", "=", self.manual_number),
            ]
            if isinstance(self.id, int):
                domain.append(("id", "!=", self.id))
            if self.search_count(domain) > 0:
                return {
                    "warning": {
                        "title": "Cảnh báo trùng số",
                        "message": f"Số công văn đi (thủ công) '{self.manual_number}' đã tồn tại hệ thống!",
                    }
                }

    # --- Sequence Logic ---
    @api.model_create_multi
    def create(self, vals_list):
        """Cấp số công văn đi ngay khi tạo (sử dụng sequence chính thức)."""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                # Ưu tiên: số thủ công
                if vals.get("is_manual_number") and vals.get("manual_number"):
                    vals["name"] = vals["manual_number"]
                else:
                    vals["name"] = (
                        self.env["ir.sequence"].next_by_code(
                            "trasas.dispatch.outgoing.official"
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
            # Tìm phòng HCNS
            hcns_dept = self.env.ref(
                "trasas_demo_users.dep_hcns", raise_if_not_found=False
            )
            if not hcns_dept:
                hcns_dept = self.env["hr.department"].search(
                    [("name", "ilike", "Hành chính")], limit=1
                )

            if not hcns_dept:
                raise ValidationError(
                    "Không tìm thấy phòng Hành chính Nhân sự. Vui lòng kiểm tra lại hệ thống phòng ban."
                )

            # Lấy tất cả nhân viên trong phòng HCNS
            hcns_employees = self.env["hr.employee"].search(
                [("department_id", "=", hcns_dept.id), ("user_id", "!=", False)]
            )
            hcns_users = hcns_employees.mapped("user_id")

            if not hcns_users:
                raise ValidationError(
                    "Phòng Hành chính Nhân sự chưa có nhân viên nào được phân quyền User."
                )

            # Tạo Activity cho TẤT CẢ nhân viên trong phòng HCNS
            for user in hcns_users:
                record.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=user.id,
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

            # Tự động hoàn thành Công văn đến liên kết (nếu có)
            if (
                record.incoming_dispatch_id
                and record.incoming_dispatch_id.state != "done"
            ):
                incoming = record.incoming_dispatch_id
                # Copy file chính thức sang response_file của CV đến
                if record.official_file and not incoming.response_file:
                    incoming.write(
                        {
                            "response_file": record.official_file,
                            "response_filename": record.official_filename
                            or "Phan_hoi_%s.pdf" % incoming.name,
                        }
                    )
                if not incoming.response_date:
                    incoming.write({"response_date": fields.Date.today()})

                # Chuyển CV đến sang Hoàn thành
                stage_done_incoming = self.env.ref(
                    "trasas_dispatch_management.stage_done", raise_if_not_found=False
                )
                if stage_done_incoming:
                    # Đóng tất cả activity còn lại
                    activity_ids = self.env["mail.activity"].search(
                        [
                            ("res_model", "=", "trasas.dispatch.incoming"),
                            ("res_id", "=", incoming.id),
                        ]
                    )
                    activity_ids.action_done()

                    incoming.write({"stage_id": stage_done_incoming.id})
                    incoming.message_post(
                        body="Công văn đến đã được tự động hoàn thành do Công văn đi phản hồi '%s' đã gửi thành công."
                        % record.name,
                        subtype_xmlid="mail.mt_note",
                    )

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
