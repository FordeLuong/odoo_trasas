from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TrasasDispatchIncoming(models.Model):
    _name = "trasas.dispatch.incoming"
    _description = "Công văn đến"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_received desc, priority desc"

    # --- Default Fields ---
    name = fields.Char(
        string="Số đến (Hệ thống)",
        required=True,
        copy=False,
        readonly=True,
        default="New",
    )
    active = fields.Boolean(default=True)

    # --- Thông tin chung ---
    dispatch_number = fields.Char(
        string="Số hiệu văn bản gốc", required=True, tracking=True
    )
    dispatch_date = fields.Date(string="Ngày văn bản", required=True, tracking=True)
    date_received = fields.Date(
        string="Ngày đến",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )

    sender_id = fields.Many2one(
        "res.partner",
        string="Nơi gửi",
        required=True,
        tracking=True,
        domain="[('is_company','=',True)]",
    )
    type_id = fields.Many2one(
        "trasas.dispatch.type", string="Loại văn bản", required=True, tracking=True
    )

    dispatch_mode = fields.Selection(
        [("hard_copy", "Bản giấy"), ("electronic", "Bản điện tử")],
        string="Hình thức",
        required=True,
        default="hard_copy",
        tracking=True,
    )

    priority = fields.Selection(
        [("normal", "Thường"), ("urgent", "Khẩn"), ("very_urgent", "Hỏa tốc")],
        string="Độ khẩn",
        default="normal",
        tracking=True,
    )

    extract_content = fields.Text(string="Trích yếu", required=True)

    # --- Đính kèm ---
    attachment_ids = fields.Many2many("ir.attachment", string="File đính kèm")
    hard_copy_location = fields.Selection(
        [
            ("a1", "Tủ A1"),
            ("a2", "Tủ A2"),
            ("a3", "Tủ A3"),
            ("b1", "Tủ B1"),
            ("b2", "Tủ B2"),
            ("b3", "Tủ B3"),
        ],
        string="Nơi lưu bản giấy",
        tracking=True,
    )

    # --- Xử lý ---
    handler_ids = fields.Many2many("res.users", string="Người xử lý", tracking=True)
    deadline = fields.Date(string="Hạn xử lý", tracking=True)
    response_required = fields.Boolean(
        string="Cần phản hồi", default=False, tracking=True
    )
    directive_note = fields.Html(string="Ý kiến chỉ đạo")

    # --- Kết quả phản hồi ---
    response_dispatch_number = fields.Char(string="Số văn bản phản hồi", tracking=True)
    response_date = fields.Date(string="Ngày phản hồi", tracking=True)

    response_file = fields.Binary(string="File phản hồi")
    response_filename = fields.Char(string="Tên file phản hồi")

    response_note = fields.Text(string="Ghi chú kết quả", tracking=True)

    # --- Status ---
    state = fields.Selection(
        [
            ("draft", "Mới"),
            ("processing", "Đang xử lý"),
            ("waiting_confirmation", "Chờ xác nhận HCNS"),
            ("done", "Hoàn thành"),
            ("cancel", "Đã hủy"),
        ],
        string="Trạng thái",
        default="draft",
        tracking=True,
        # group_expand="_expand_states",  # Uncomment after server restart
    )

    # --- Computed ---
    is_overdue = fields.Boolean(
        string="Quá hạn", compute="_compute_is_overdue", store=True
    )
    overdue_days = fields.Integer(
        string="Số ngày quá hạn", compute="_compute_is_overdue"
    )

    @api.depends("state", "deadline")
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            if (
                record.state in ("processing", "waiting_confirmation")
                and record.deadline
                and record.deadline < today
            ):
                record.is_overdue = True
                record.overdue_days = (today - record.deadline).days
            else:
                record.is_overdue = False
                record.overdue_days = 0

    @api.model
    def _expand_states(self, states, domain, *args):
        """Expand states to show all stages in kanban view"""
        return [key for key, val in type(self).state.selection]

    # --- Constraints ---
    _sql_constraints = [
        (
            "dispatch_number_uniq",
            "unique(dispatch_number)",
            "Số hiệu văn bản này đã tồn tại trong hệ thống!",
        ),
    ]

    @api.constrains("dispatch_date", "date_received", "deadline")
    def _check_dates(self):
        for record in self:
            if (
                record.dispatch_date
                and record.date_received
                and record.dispatch_date > record.date_received
            ):
                raise ValidationError(
                    f"Ngày văn bản ({record.dispatch_date}) không được lớn hơn Ngày đến ({record.date_received})!"
                )
            if (
                record.date_received
                and record.deadline
                and record.date_received > record.deadline
            ):
                raise ValidationError(
                    f"Ngày đến ({record.date_received}) không được lớn hơn Hạn xử lý ({record.deadline})!"
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("trasas.dispatch.incoming")
                    or "New"
                )
        return super().create(vals_list)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    # --- Actions ---
    def action_confirm(self):
        """Chuyển sang trạng thái Đang xử lý và gửi thông báo"""
        for record in self:
            if record.response_required and not record.handler_ids:
                from odoo.exceptions import UserError

                raise UserError(
                    "Vui lòng chọn Người xử lý trước khi tiếp nhận công văn cần phản hồi!"
                )

            # Kiểm tra file đính kèm
            if not record.attachment_ids:
                from odoo.exceptions import UserError as UE

                raise UE("Vui lòng đính kèm file công văn trước khi tiếp nhận!")

            record.state = "processing"

            # Tạo hoạt động cho người xử lý
            if record.handler_ids:
                user_ids = record.handler_ids.ids

                # Gửi email template "Phân công xử lý"
                template = self.env.ref(
                    "trasas_dispatch_management.email_template_dispatch_assigned",
                    raise_if_not_found=False,
                )
                if template:
                    for user in record.handler_ids:
                        template.send_mail(record.id, force_send=True)

                # Tạo Activity
                activity_type = self.env.ref(
                    "mail.mail_activity_data_todo", raise_if_not_found=False
                )
                if not activity_type:
                    activity_type = self.env["mail.activity.type"].search([], limit=1)

                for user_id in user_ids:
                    self.env["mail.activity"].create(
                        {
                            "res_model_id": self.env["ir.model"]._get_id(self._name),
                            "res_id": record.id,
                            "activity_type_id": activity_type.id,
                            "summary": f"Xử lý công văn: {record.dispatch_number}",
                            "note": f"Được giao xử lý công văn số {record.dispatch_number}. Vui lòng kiểm tra và phản hồi trước {record.deadline or 'không có hạn'}.",
                            "user_id": user_id,
                            "date_deadline": record.deadline or fields.Date.today(),
                        }
                    )

    def action_done(self):
        """Hoàn thành công văn (chỉ dùng cho công văn không cần phản hồi)"""
        for record in self:
            # Nếu cần phản hồi, phải dùng workflow submit → confirm
            if record.response_required:
                from odoo.exceptions import UserError

                raise UserError(
                    "Công văn yêu cầu phản hồi! Vui lòng sử dụng nút 'Gửi phản hồi' để submit văn bản phản hồi."
                )

            record.state = "done"

            # Mark done activities
            activity_ids = self.env["mail.activity"].search(
                [("res_model", "=", self._name), ("res_id", "=", record.id)]
            )
            activity_ids.action_done()

            record.message_post(
                body="Công văn đã hoàn thành và lưu trữ.", subtype_xmlid="mail.mt_note"
            )

    def action_cancel(self):
        for record in self:
            record.state = "cancel"
            record.message_post(
                body="Công văn đã bị hủy bỏ.", subtype_xmlid="mail.mt_note"
            )

    def action_draft(self):
        for record in self:
            record.state = "draft"
            record.message_post(
                body="Công văn đã được chuyển về nháp.", subtype_xmlid="mail.mt_note"
            )

    def action_submit_response(self):
        """Người xử lý submit phản hồi"""
        for record in self:
            # Auto-generate response number if missing
            if not record.response_dispatch_number:
                record.response_dispatch_number = self.env["ir.sequence"].next_by_code(
                    "trasas.dispatch.response"
                )

            # Validation
            if not record.response_file:
                from odoo.exceptions import ValidationError

                raise ValidationError("Vui lòng đính kèm 'File phản hồi'!")

            record.state = "waiting_confirmation"
            if not record.response_date:
                record.response_date = fields.Date.today()

            # Mark done activity for current user (Handler)
            activity_ids = self.env["mail.activity"].search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", record.id),
                    ("user_id", "=", self.env.user.id),
                ]
            )
            if activity_ids:
                activity_ids.action_done()

            # Ghi log vào Chatter
            record.message_post(
                body=f"Văn bản phản hồi đã được submit bởi {self.env.user.name}. Đang chờ HCNS xác nhận.",
                subtype_xmlid="mail.mt_comment",
            )

            # --- Activity cho HCNS ---
            # Tìm nhóm HCNS (giả sử dùng group_dispatch_user hoặc admin nếu chưa có group riêng)
            # Tạm thời gửi cho Admin hoặc người tạo nếu không có nhóm cụ thể
            # hcns_users = record.env.ref("base.group_user").users  # TODO: Thay bằng group HCNS thực tế
            # Để tránh spam, ở đây lấy người tạo làm đại diện HCNS (nếu người tạo có quyền)
            # Hoặc tốt nhất là define 1 group HCNS trong XML

            # Gửi email template "Đã có phản hồi"
            template = self.env.ref(
                "trasas_dispatch_management.email_template_dispatch_response_submitted",
                raise_if_not_found=False,
            )
            # Gửi cho người tạo (giả định là HCNS tiếp nhận ban đầu)
            if template and record.create_uid.partner_id:
                template.send_mail(record.id, force_send=True)

            # Tạo Activity cho người tạo (HCNS)
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=record.create_uid.id,
                summary=f"Kiểm tra phản hồi: {record.dispatch_number}",
                note="Người xử lý đã gửi phản hồi. Vui lòng kiểm tra và xác nhận.",
                date_deadline=fields.Date.today(),
            )

    def action_confirm_response(self):
        """HCNS xác nhận đã nhận phản hồi"""
        for record in self:
            record.state = "done"

            # Mark done activities
            activity_ids = self.env["mail.activity"].search(
                [("res_model", "=", self._name), ("res_id", "=", record.id)]
            )
            activity_ids.action_done()

            # Gửi email template "Hoàn thành"
            template = self.env.ref(
                "trasas_dispatch_management.email_template_dispatch_completed",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

            record.message_post(
                body="HCNS đã xác nhận văn bản phản hồi. Công văn hoàn thành.",
                subtype_xmlid="mail.mt_note",
            )

    def action_generate_response_number(self):
        """Generate response number based on sequence"""
        for record in self:
            if not record.response_dispatch_number:
                record.response_dispatch_number = self.env["ir.sequence"].next_by_code(
                    "trasas.dispatch.response"
                )

    @api.model
    def check_overdue_deadline(self):
        """Cron Job: Kiểm tra công văn quá hạn và gửi cảnh báo"""
        today = fields.Date.today()
        # Tìm các công văn đang xử lý hoặc chờ xác nhận và quá hạn
        overdue_records = self.search(
            [
                ("state", "in", ["processing", "waiting_confirmation"]),
                ("deadline", "<", today),
                ("deadline", "!=", False),
            ]
        )

        for record in overdue_records:
            # Gửi email cảnh báo
            # Gửi email template "Cảnh báo quá hạn"
            template = self.env.ref(
                "trasas_dispatch_management.email_template_dispatch_overdue",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)
