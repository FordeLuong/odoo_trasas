from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class TrasasDispatchIncoming(models.Model):
    _name = "trasas.dispatch.incoming"
    _description = "Công văn đến"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_received desc, urgency_id desc"

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
    is_manual_number = fields.Boolean(string="Cấp số thủ công", tracking=True)
    manual_number = fields.Char(string="Số CV (Thủ công)", tracking=True)
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

    urgency_id = fields.Many2one(
        "trasas.dispatch.urgency",
        string="Độ khẩn",
        default=lambda self: self.env.ref(
            "trasas_dispatch_management.urgency_normal", raise_if_not_found=False
        ),
        tracking=True,
    )

    extract_content = fields.Text(string="Trích yếu", required=True)

    # --- Đính kèm ---
    attachment_ids = fields.Many2many("ir.attachment", string="File đính kèm")

    document_folder_id = fields.Many2one(
        "documents.document",
        string="Thư mục tài liệu (Documents)",
        domain="[('type', '=', 'folder')]",
        readonly=True,
    )
    location_id = fields.Many2one(
        "trasas.dispatch.location",
        string="Nơi lưu bản giấy",
        tracking=True,
    )

    # --- Xử lý ---
    is_via_manager = fields.Boolean(string="Chỉ định qua Quản lý", tracking=True)
    manager_id = fields.Many2one(
        "res.users",
        string="Trưởng/Phó phòng",
        domain="[('share', '=', False)]",
        tracking=True,
    )
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

    # --- Stage (Dynamic) ---
    stage_id = fields.Many2one(
        "trasas.dispatch.stage",
        string="Giai đoạn",
        tracking=True,
        default=lambda self: self._default_stage_id(),
        group_expand="_read_group_stage_ids",
        index=True,
        copy=False,
    )

    # Computed state from stage flags (for backward compatibility)
    state = fields.Selection(
        [
            ("draft", "Mới"),
            ("manager_assign", "Chờ quản lý phân công"),
            ("processing", "Đang xử lý"),
            ("waiting_confirmation", "Chờ xác nhận HCNS"),
            ("done", "Hoàn thành"),
            ("cancel", "Đã hủy"),
        ],
        string="Trạng thái",
        compute="_compute_state",
        store=True,
        tracking=True,
    )

    # --- Computed ---
    can_assign_manager = fields.Boolean(
        string="Có quyền phân công", compute="_compute_can_assign_manager"
    )

    def _compute_can_assign_manager(self):
        is_admin_or_reviewer = self.env.user.has_group(
            "trasas_dispatch_management.group_dispatch_administrator"
        ) or self.env.user.has_group(
            "trasas_dispatch_management.group_dispatch_reviewer"
        )
        for record in self:
            record.can_assign_manager = is_admin_or_reviewer or (
                record.manager_id and record.manager_id == self.env.user
            )

    is_overdue = fields.Boolean(
        string="Quá hạn", compute="_compute_is_overdue", store=True
    )
    overdue_days = fields.Integer(
        string="Số ngày quá hạn", compute="_compute_is_overdue"
    )

    def _default_stage_id(self):
        """Get the default draft stage"""
        return self.env["trasas.dispatch.stage"].search(
            [("is_draft", "=", True)], limit=1
        )

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Show all stages in kanban view"""
        return self.env["trasas.dispatch.stage"].search([], order="sequence")

    @api.depends(
        "stage_id", "stage_id.is_draft", "stage_id.is_done", "stage_id.is_cancel"
    )
    def _compute_state(self):
        """Derive state from stage flags for backward compatibility"""
        stage_draft = self.env.ref(
            "trasas_dispatch_management.stage_draft", raise_if_not_found=False
        )
        stage_processing = self.env.ref(
            "trasas_dispatch_management.stage_processing", raise_if_not_found=False
        )
        stage_waiting = self.env.ref(
            "trasas_dispatch_management.stage_waiting", raise_if_not_found=False
        )
        stage_manager_assign = self.env.ref(
            "trasas_dispatch_management.stage_manager_assign", raise_if_not_found=False
        )
        for record in self:
            if not record.stage_id:
                record.state = "draft"
            elif record.stage_id.is_cancel:
                record.state = "cancel"
            elif record.stage_id.is_done:
                record.state = "done"
            elif record.stage_id == stage_manager_assign:
                record.state = "manager_assign"
            elif record.stage_id == stage_waiting:
                record.state = "waiting_confirmation"
            elif record.stage_id == stage_draft:
                record.state = "draft"
            elif record.stage_id == stage_processing:
                record.state = "processing"
            else:
                # Custom stages default to processing
                record.state = "processing"

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

    # --- Constraints ---
    _sql_constraints = [
        (
            "dispatch_number_uniq",
            "unique(dispatch_number)",
            "Số hiệu văn bản này đã tồn tại trong hệ thống!",
        ),
    ]

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
                        "message": f"Số công văn thủ công '{self.manual_number}' đã tồn tại trong hệ thống!",
                    }
                }
            self.dispatch_number = self.manual_number

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
            if vals.get("name", "New") == "New" or vals.get("name") == _("New"):
                if vals.get("is_manual_number") and vals.get("manual_number"):
                    vals["name"] = vals["manual_number"]
                    if not vals.get("dispatch_number"):
                        vals["dispatch_number"] = vals["manual_number"]
                else:
                    vals["name"] = self.env["ir.sequence"].next_by_code(
                        "trasas.dispatch.incoming"
                    ) or _("New")
        records = super().create(vals_list)
        records._create_document_folder()
        return records

    def write(self, vals):
        res = super().write(vals)

        if "name" in vals or "dispatch_number" in vals:
            for rec in self:
                if rec.document_folder_id:
                    folder_name = (
                        f"{rec.name}_{rec.dispatch_number}"
                        if rec.name and rec.dispatch_number
                        else rec.name or rec.dispatch_number
                    )
                    rec.document_folder_id.sudo().write({"name": folder_name})

        # Xử lý sync file
        if any(f in vals for f in ["attachment_ids", "response_file"]):
            for rec in self:
                if vals.get("response_file"):
                    rec._create_attachment_from_binary(
                        vals.get("response_file"),
                        vals.get("response_filename") or f"Phan_hoi_{rec.name}.pdf",
                    )
                rec._sync_attachments_to_document()

        return res

    def _create_attachment_from_binary(self, file_content, file_name):
        """Tạo ir.attachment từ trường binary nếu chưa có"""
        self.ensure_one()
        if not file_content:
            return

        Attachment = self.env["ir.attachment"].sudo()
        existing = Attachment.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("name", "=", file_name),
            ],
            limit=1,
        )

        if not existing:
            Attachment.create(
                {
                    "name": file_name,
                    "type": "binary",
                    "datas": file_content,
                    "res_model": self._name,
                    "res_id": self.id,
                }
            )

    def _create_document_folder(self):
        Document = self.env["documents.document"].sudo()
        type_folders = self.mapped("type_id.document_folder_id")
        root_incoming = type_folders.mapped("folder_id")[:1] if type_folders else False

        for rec in self:
            if rec.document_folder_id:
                continue

            folder_name = (
                f"{rec.name}_{rec.dispatch_number}"
                if rec.name and rec.dispatch_number
                else rec.name or rec.dispatch_number
            )

            parent_id = False
            if rec.is_manual_number:
                if root_incoming:
                    manual_parent = Document.search(
                        [
                            ("name", "=", "Công văn đến (Thủ công)"),
                            ("type", "=", "folder"),
                            ("folder_id", "=", root_incoming.id),
                        ],
                        limit=1,
                    )
                    if not manual_parent:
                        manual_parent = Document.create(
                            {
                                "name": "Công văn đến (Thủ công)",
                                "type": "folder",
                                "folder_id": root_incoming.id,
                            }
                        )
                    parent_id = manual_parent.id
            elif rec.type_id and rec.type_id.document_folder_id:
                parent_id = rec.type_id.document_folder_id.id

            if parent_id:
                folder = Document.create(
                    {
                        "name": folder_name,
                        "type": "folder",
                        "folder_id": parent_id,
                    }
                )
                rec.write({"document_folder_id": folder.id})

    @api.model
    def _create_folders_for_existing(self):
        records = self.search([("document_folder_id", "=", False)])
        records._create_document_folder()
        for rec in self.search([]):
            if rec.response_file:
                rec._create_attachment_from_binary(
                    rec.response_file,
                    rec.response_filename or f"Phan_hoi_{rec.name}.pdf",
                )
            rec._sync_attachments_to_document()

    def _sync_attachments_to_document(self):
        """Đồng bộ các file đính kèm của Công văn sang ứng dụng Documents"""
        self.ensure_one()
        if not self.document_folder_id:
            return

        Document = self.env["documents.document"].sudo()
        Attachment = self.env["ir.attachment"].sudo()

        domain = [
            ("res_model", "=", self._name),
            ("res_id", "=", self.id),
        ]
        attachments = Attachment.search(domain)

        for attachment in attachments:
            existing = Document.search([("attachment_id", "=", attachment.id)], limit=1)
            if not existing:
                Document.create(
                    {
                        "attachment_id": attachment.id,
                        "folder_id": self.document_folder_id.id,
                        "name": attachment.name,
                        "confidential_level": "public",
                    }
                )

    def action_view_documents(self):
        """Mở danh sách file đính kèm của Công văn"""
        self.ensure_one()

        return {
            "name": _("Hồ sơ / Tài liệu"),
            "type": "ir.actions.act_window",
            "res_model": "ir.attachment",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
        }

    # --- Helper: get stage by XML ID ---
    def _get_stage(self, xmlid):
        """Get a stage by its XML ID"""
        return self.env.ref(
            f"trasas_dispatch_management.{xmlid}", raise_if_not_found=False
        )

    # --- Actions ---
    def action_confirm(self):
        """Chuyển sang giai đoạn Đang xử lý (hoặc chờ Quản lý phân công) và gửi thông báo"""
        stage_processing = self._get_stage("stage_processing")
        stage_manager_assign = self._get_stage("stage_manager_assign")
        if not stage_processing or not stage_manager_assign:
            raise UserError(
                "Chưa cấu hình giai đoạn 'Đang xử lý' hoặc 'Chờ quản lý phân công'!"
            )

        for record in self:
            # Kiểm tra file đính kèm
            if not record.attachment_ids:
                raise UserError("Vui lòng đính kèm file công văn trước khi tiếp nhận!")

            if record.is_via_manager:
                if not record.manager_id:
                    raise UserError(
                        "Vui lòng chọn Trưởng/Phó phòng khi tích 'Chỉ định qua Quản lý'!"
                    )

                record.stage_id = stage_manager_assign

                # Tạo Activity cho quản lý
                activity_type = self.env.ref(
                    "mail.mail_activity_data_todo", raise_if_not_found=False
                )
                if not activity_type:
                    activity_type = self.env["mail.activity.type"].search([], limit=1)

                self.env["mail.activity"].create(
                    {
                        "res_model_id": self.env["ir.model"]._get_id(self._name),
                        "res_id": record.id,
                        "activity_type_id": activity_type.id,
                        "summary": f"Yêu cầu phân công: {record.dispatch_number or record.name}",
                        "note": f"Vui lòng phân công người xử lý cho công văn số {record.dispatch_number or record.name}.",
                        "user_id": record.manager_id.id,
                        "date_deadline": record.deadline or fields.Date.today(),
                    }
                )
            else:
                if record.response_required and not record.handler_ids:
                    raise UserError(
                        "Vui lòng chọn Người xử lý trước khi tiếp nhận công văn cần phản hồi!"
                    )

                record.stage_id = stage_processing

                # Tạo hoạt động cho người xử lý
                if record.handler_ids:
                    # Gửi email template nếu stage có cấu hình
                    if stage_processing.mail_template_id:
                        for user in record.handler_ids:
                            stage_processing.mail_template_id.send_mail(
                                record.id, force_send=True
                            )
                    else:
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
                        activity_type = self.env["mail.activity.type"].search(
                            [], limit=1
                        )

                    for user_id in record.handler_ids.ids:
                        self.env["mail.activity"].create(
                            {
                                "res_model_id": self.env["ir.model"]._get_id(
                                    self._name
                                ),
                                "res_id": record.id,
                                "activity_type_id": activity_type.id,
                                "summary": f"Xử lý công văn: {record.dispatch_number or record.name}",
                                "note": f"Được giao xử lý công văn số {record.dispatch_number or record.name}. Vui lòng kiểm tra và phản hồi trước {record.deadline or 'không có hạn'}.",
                                "user_id": user_id,
                                "date_deadline": record.deadline or fields.Date.today(),
                            }
                        )

    def action_manager_assign(self):
        """Quản lý đã chọn người xử lý và tiến hành phân công"""
        stage_processing = self._get_stage("stage_processing")
        if not stage_processing:
            raise UserError("Chưa cấu hình giai đoạn 'Đang xử lý'!")

        for record in self:
            if not record.can_assign_manager:
                raise UserError(
                    "Chỉ Quản lý được chỉ định hoặc Quản trị viên mới có quyền thực hiện thao tác này!"
                )

            if not record.handler_ids:
                raise UserError("Vui lòng chọn Người xử lý trước khi phân công!")

            record.stage_id = stage_processing

            # Mark activity "Phân công xử lý" của manager là done
            manager_activities = self.env["mail.activity"].search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", record.id),
                    ("user_id", "=", self.env.user.id),
                ]
            )
            manager_activities.action_done()

            # Tạo hoạt động cho người xử lý mới
            if stage_processing.mail_template_id:
                for user in record.handler_ids:
                    stage_processing.mail_template_id.send_mail(
                        record.id, force_send=True
                    )
            else:
                template = self.env.ref(
                    "trasas_dispatch_management.email_template_dispatch_assigned",
                    raise_if_not_found=False,
                )
                if template:
                    for user in record.handler_ids:
                        template.send_mail(record.id, force_send=True)

            activity_type = self.env.ref(
                "mail.mail_activity_data_todo", raise_if_not_found=False
            )
            if not activity_type:
                activity_type = self.env["mail.activity.type"].search([], limit=1)

            for user_id in record.handler_ids.ids:
                self.env["mail.activity"].create(
                    {
                        "res_model_id": self.env["ir.model"]._get_id(self._name),
                        "res_id": record.id,
                        "activity_type_id": activity_type.id,
                        "summary": f"Xử lý công văn: {record.dispatch_number or record.name}",
                        "note": f"Phân công từ Quản lý: Vui lòng kiểm tra và phản hồi công văn số {record.dispatch_number or record.name} trước {record.deadline or 'không có hạn'}.",
                        "user_id": user_id,
                        "date_deadline": record.deadline or fields.Date.today(),
                    }
                )

    def action_done(self):
        """Hoàn thành công văn (chỉ dùng cho công văn không cần phản hồi)"""
        stage_done = self._get_stage("stage_done")
        if not stage_done:
            raise UserError("Chưa cấu hình giai đoạn 'Hoàn thành'!")

        for record in self:
            if record.response_required:
                raise UserError(
                    "Công văn yêu cầu phản hồi! Vui lòng sử dụng nút 'Gửi phản hồi' để submit văn bản phản hồi."
                )

            record.stage_id = stage_done

            # Mark done activities
            activity_ids = self.env["mail.activity"].search(
                [("res_model", "=", self._name), ("res_id", "=", record.id)]
            )
            activity_ids.action_done()

            record.message_post(
                body="Công văn đã hoàn thành và lưu trữ.", subtype_xmlid="mail.mt_note"
            )

    def action_cancel(self):
        stage_cancel = self._get_stage("stage_cancel")
        if not stage_cancel:
            raise UserError("Chưa cấu hình giai đoạn 'Hủy'!")

        for record in self:
            record.stage_id = stage_cancel
            record.message_post(
                body="Công văn đã bị hủy bỏ.", subtype_xmlid="mail.mt_note"
            )

    def action_draft(self):
        stage_draft = self._get_stage("stage_draft")
        if not stage_draft:
            raise UserError("Chưa cấu hình giai đoạn 'Mới'!")

        for record in self:
            record.stage_id = stage_draft
            record.message_post(
                body="Công văn đã được chuyển về nháp.", subtype_xmlid="mail.mt_note"
            )

    def action_submit_response(self):
        """Người xử lý submit phản hồi"""
        stage_waiting = self._get_stage("stage_waiting")
        if not stage_waiting:
            raise UserError("Chưa cấu hình giai đoạn 'Chờ xác nhận'!")

        for record in self:
            # Auto-generate response number if missing
            if not record.response_dispatch_number:
                record.response_dispatch_number = self.env["ir.sequence"].next_by_code(
                    "trasas.dispatch.response"
                )

            # Validation
            if not record.response_file:
                raise ValidationError("Vui lòng đính kèm 'File phản hồi'!")

            record.stage_id = stage_waiting
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

            # Gửi email template (từ stage hoặc fallback)
            template = stage_waiting.mail_template_id or self.env.ref(
                "trasas_dispatch_management.email_template_dispatch_response_submitted",
                raise_if_not_found=False,
            )
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
        stage_done = self._get_stage("stage_done")
        if not stage_done:
            raise UserError("Chưa cấu hình giai đoạn 'Hoàn thành'!")

        for record in self:
            record.stage_id = stage_done

            # Mark done activities
            activity_ids = self.env["mail.activity"].search(
                [("res_model", "=", self._name), ("res_id", "=", record.id)]
            )
            activity_ids.action_done()

            # Gửi email
            template = stage_done.mail_template_id or self.env.ref(
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
        overdue_records = self.search(
            [
                ("state", "in", ["processing", "waiting_confirmation"]),
                ("deadline", "<", today),
                ("deadline", "!=", False),
            ]
        )

        for record in overdue_records:
            template = self.env.ref(
                "trasas_dispatch_management.email_template_dispatch_overdue",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)
