# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class TrasasContract(models.Model):
    """Model chính - Quản lý hợp đồng TRASAS"""

    _name = "trasas.contract"
    _description = "Hợp đồng TRASAS"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    # ============ KANBAN STAGE ============
    stage_id = fields.Many2one(
        "trasas.contract.stage",
        string="Giai đoạn",
        tracking=True,
        index=True,
        copy=False,
        group_expand="_read_group_stage_ids",
        default=lambda self: self.env.ref(
            "trasas_contract_management.stage_draft", raise_if_not_found=False
        ),
        help="Giai đoạn hiện tại của hợp đồng (dùng cho Kanban)",
    )

    # ============ COMPUTED: PHÂN QUYỀN HIỂN THỊ NÚT ============
    is_approver = fields.Boolean(
        string="Is Approver",
        compute="_compute_is_approver",
        help="True nếu user hiện tại thuộc nhóm Approver (Giám đốc)",
    )

    is_reviewer = fields.Boolean(
        string="Is Reviewer",
        compute="_compute_is_reviewer",
        help="True nếu user hiện tại là người được giao rà soát hợp đồng này",
    )

    is_current_approver = fields.Boolean(
        string="Is Current Approver",
        compute="_compute_is_current_approver",
        help="True nếu user hiện tại là người đang được giao phê duyệt hợp đồng này",
    )

    is_operation_user = fields.Boolean(
        string="Is Operation User",
        compute="_compute_is_operation_user",
        help="True nếu user hiện tại thuộc nhóm Vận hành và KHÔNG thuộc nhóm HCNS/Lãnh đạo",
    )

    kanban_state = fields.Selection(
        [
            ("normal", "Bình thường"),
            ("done", "Hoàn tất"),
            ("blocked", "Bị chặn"),
        ],
        string="Trạng thái Kanban",
        default="normal",
        tracking=True,
        help="Trạng thái phụ cho kanban card",
    )

    color = fields.Integer(string="Màu", default=0)

    priority = fields.Selection(
        [
            ("0", "Bình thường"),
            ("1", "Tốt"),
            ("2", "Rất tốt"),
            ("3", "Xuất sắc"),
        ],
        string="Mức ưu tiên",
        default="0",
    )

    legend_normal = fields.Char(
        related="stage_id.legend_normal", string="Kanban: Bình thường", readonly=True
    )
    legend_blocked = fields.Char(
        related="stage_id.legend_blocked", string="Kanban: Bị chặn", readonly=True
    )
    legend_done = fields.Char(
        related="stage_id.legend_done", string="Kanban: Hoàn tất", readonly=True
    )

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Hiển thị tất cả stage trong Kanban kể cả khi trống"""
        return self.env["trasas.contract.stage"].search([], order="sequence")

    def init(self):
        """Gán stage cho hợp đồng cũ chưa có stage_id (chạy khi upgrade)"""
        state_to_xmlid = {
            "draft": "stage_draft",
            "in_review": "stage_in_review",
            "waiting": "stage_waiting",
            "approved": "stage_approved",
            "signing": "stage_signing",
            "signed": "stage_signed",
            "archived": "stage_archived",
            "expired": "stage_expired",
            "cancel": "stage_cancel",
        }
        for state, xmlid in state_to_xmlid.items():
            stage = self.env.ref(
                f"trasas_contract_management.{xmlid}", raise_if_not_found=False
            )
            if stage:
                self.env.cr.execute(
                    """
                    UPDATE trasas_contract
                    SET stage_id = %s
                    WHERE state = %s AND (stage_id IS NULL)
                    """,
                    (stage.id, state),
                )

    # ============ THÔNG TIN ĐỊNH DANH ============
    name = fields.Char(
        string="Số hợp đồng",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        tracking=True,
        help="Số hợp đồng sẽ được tạo tự động",
    )

    contract_type_id = fields.Many2one(
        "trasas.contract.type",
        string="Loại hợp đồng",
        required=True,
        tracking=True,
        help="Chọn loại hợp đồng",
    )

    tag_ids = fields.Many2many(
        "trasas.contract.tag",
        string="Thẻ hợp đồng",
        help="Gắn nhãn phân loại nhanh cho hợp đồng",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Đối tác",
        required=True,
        tracking=True,
        help="Đối tác ký kết hợp đồng",
    )

    title = fields.Char(
        string="Tiêu đề hợp đồng",
        required=True,
        tracking=True,
        help="Tiêu đề ngắn gọn của hợp đồng",
    )

    description = fields.Text(string="Mô tả", help="Mô tả chi tiết nội dung hợp đồng")

    document_folder_id = fields.Many2one(
        "documents.document",
        string="Folder tài liệu",
        domain="[('type', '=', 'folder')]",
        readonly=True,
    )

    # ============ LUỒNG KÝ ============
    signing_flow = fields.Selection(
        [
            ("trasas_first", "TRASAS ký trước"),
            ("partner_first", "Đối tác ký trước"),
        ],
        string="Luồng ký",
        default="trasas_first",
        required=True,
        tracking=True,
        help="Quy định bên nào ký trước",
    )

    # ============ CÁC MỐC THỜI GIAN ============
    sign_deadline = fields.Date(
        string="Hạn ký", tracking=True, help="Ngày hết hạn để hoàn tất ký kết"
    )

    date_start = fields.Date(
        string="Ngày bắt đầu",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Ngày bắt đầu hiệu lực hợp đồng",
    )

    date_end = fields.Date(
        string="Ngày kết thúc",
        required=True,
        tracking=True,
        help="Ngày kết thúc hiệu lực hợp đồng",
    )

    duration_days = fields.Integer(
        string="Thời hạn (ngày)",
        compute="_compute_duration_days",
        store=True,
        help="Số ngày hiệu lực của hợp đồng",
    )

    days_to_expire = fields.Integer(
        string="Còn lại (ngày)",
        compute="_compute_days_to_expire",
        help="Số ngày còn lại đến khi hết hạn",
    )

    # ============ QUẢN LÝ FILE ============
    final_scan_file = fields.Binary(
        string="Bản scan cuối cùng",
        attachment=True,
        help="File PDF bản scan sau khi đã đóng dấu (chỉ HCNS mới upload được)",
    )

    storage_location = fields.Char(
        string="Vị trí lưu kho",
        tracking=True,
        help="Vị trí lưu trữ bản cứng (VD: Tủ A, Kệ 2)",
    )

    final_scan_filename = fields.Char(string="Tên file scan")

    appendix_ids = fields.One2many(
        "trasas.contract.appendix", "contract_id", string="Phụ lục"
    )

    # ============ ODOO SIGN INTEGRATION ============
    sign_request_ids = fields.One2many(
        "sign.request", "contract_id", string="Yêu cầu ký"
    )
    sign_request_count = fields.Integer(
        string="Số yêu cầu ký", compute="_compute_sign_request_count"
    )

    # ============ TRẠNG THÁI ============
    state = fields.Selection(
        [
            ("draft", "Nháp"),
            ("in_review", "Đang rà soát"),
            ("waiting", "Chờ duyệt"),
            ("approved", "Đã duyệt"),
            ("signing", "Đang ký"),
            ("signed", "Đã ký"),
            ("archived", "Đã lưu kho"),
            ("expired", "Hết hạn"),
            ("cancel", "Đã hủy"),
        ],
        string="Trạng thái",
        default="draft",
        required=True,
        tracking=True,
        help="Trạng thái hiện tại của hợp đồng",
    )

    # ============ NGƯỜI LIÊN QUAN ============
    user_id = fields.Many2one(
        "res.users",
        string="Người tạo",
        default=lambda self: self.env.user,
        tracking=True,
        help="Nhân viên tạo hợp đồng",
    )

    approver_id = fields.Many2one(
        "res.users",
        string="Người phê duyệt",
        tracking=True,
        help="Giám đốc phê duyệt hợp đồng",
    )

    reviewer_id = fields.Many2one(
        "res.users",
        string="Người rà soát",
        tracking=True,
        help="Người rà soát trước khi trình ký (VD: Trưởng bộ phận, Pháp chế)",
    )

    suggested_reviewer_id = fields.Many2one(
        "res.users",
        string="Người rà soát đề xuất",
        tracking=True,
        help="Người dùng có thể chọn người rà soát khi gửi hợp đồng. Nếu không chọn, hệ thống sẽ gửi cho Trưởng bộ phận.",
    )

    suggested_approver_id = fields.Many2one(
        "res.users",
        string="Người phê duyệt đề xuất",
        domain=lambda self: [
            "|",
            (
                "group_ids",
                "in",
                [self.env.ref("trasas_contract_management.group_contract_reviewer").id],
            ),
            (
                "group_ids",
                "in",
                [self.env.ref("trasas_contract_management.group_contract_approver").id],
            ),
        ],
        tracking=True,
        help="Chọn người phê duyệt từ nhóm Ban Giám đốc hoặc GĐ Nghiệp vụ",
    )

    approved_date = fields.Datetime(
        string="Ngày phê duyệt", readonly=True, tracking=True
    )

    review_date = fields.Datetime(string="Ngày rà soát", readonly=True, tracking=True)

    contract_date = fields.Date(
        string="Ngày tạo",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
        help="Ngày tạo hợp đồng (mặc định là ngày hiện tại)",
    )

    signed_date = fields.Date(string="Ngày ký kết", readonly=True, tracking=True)

    company_id = fields.Many2one(
        "res.company", string="Công ty", default=lambda self: self.env.company
    )

    # ============ TRACKING KÝ KẾT (Chi tiết) ============
    internal_sign_date = fields.Datetime(
        string="Ngày nội bộ ký",
        readonly=True,
        tracking=True,
        help="Ngày Giám đốc/Thẩm quyền TRASAS ký",
    )
    sent_to_partner_date = fields.Date(
        string="Ngày gửi đối tác",
        readonly=True,
        tracking=True,
        help="Ngày gửi hợp đồng cho đối tác",
    )
    partner_sign_date = fields.Date(
        string="Ngày đối tác ký",
        readonly=True,
        tracking=True,
        help="Ngày đối tác ký hợp đồng (nếu có)",
    )

    final_scan_file = fields.Binary(
        string="Bản scan đã ký", attachment=True, help="File scan hợp đồng có đủ chữ ký"
    )
    final_scan_filename = fields.Char(string="Tên file scan")

    stamped_file = fields.Binary(
        string="Bản đóng dấu",
        attachment=True,
        help="Bản scan hợp đồng đã đóng dấu đỏ (Final)",
    )
    stamped_filename = fields.Char(string="Tên file đóng dấu")

    active = fields.Boolean(
        string="Active", default=True, help="Bỏ chọn để archive hợp đồng"
    )

    # ============ GHI CHÚ ============
    notes = fields.Html(
        string="Ghi chú nội bộ", help="Ghi chú chỉ dành cho nội bộ TRASAS"
    )

    rejection_reason = fields.Text(
        string="Lý do từ chối",
        readonly=True,
        tracking=True,
        help="Lý do giám đốc từ chối phê duyệt",
    )

    # ============ CANCEL REQUEST WORKFLOW ============
    cancel_request_state = fields.Selection(
        [
            ("none", "Không có"),
            ("dept_pending", "Chờ Trưởng phòng"),
            ("bgd_pending", "Chờ Ban Giám đốc"),
            ("approved", "Đã duyệt hủy"),
            ("rejected", "Từ chối hủy"),
        ],
        string="Trạng thái yêu cầu hủy",
        default="none",
        tracking=True,
    )
    cancel_reason = fields.Text(
        string="Lý do hủy",
        tracking=True,
    )
    cancel_requester_id = fields.Many2one(
        "res.users",
        string="Người yêu cầu hủy",
        readonly=True,
    )
    cancel_dept_approver_id = fields.Many2one(
        "res.users",
        string="Trưởng phòng duyệt hủy",
        readonly=True,
    )
    cancel_bgd_approver_id = fields.Many2one(
        "res.users",
        string="BGĐ duyệt hủy",
        readonly=True,
    )
    is_cancel_dept_approver = fields.Boolean(
        string="Is Cancel Dept Approver",
        compute="_compute_is_cancel_dept_approver",
    )

    # ============ YÊU CẦU ĐẶT VỀ NHÁP ============
    draft_request_state = fields.Selection(
        [
            ("none", "Không có"),
            ("dept_pending", "Chờ Trưởng phòng"),
            ("bgd_pending", "Chờ Ban Giám đốc"),
            ("approved", "Đã duyệt về nháp"),
            ("rejected", "Từ chối về nháp"),
        ],
        string="Trạng thái yêu cầu về nháp",
        default="none",
        tracking=True,
    )
    draft_reason = fields.Text(
        string="Lý do về nháp",
        tracking=True,
    )
    draft_requester_id = fields.Many2one(
        "res.users",
        string="Người yêu cầu về nháp",
        readonly=True,
    )
    draft_dept_approver_id = fields.Many2one(
        "res.users",
        string="Trưởng phòng duyệt nháp",
        readonly=True,
    )
    draft_bgd_approver_id = fields.Many2one(
        "res.users",
        string="BGĐ duyệt nháp",
        readonly=True,
    )
    is_draft_dept_approver = fields.Boolean(
        string="Is Draft Dept Approver",
        compute="_compute_is_draft_dept_approver",
    )

    # ============ COMPUTED FIELDS ============
    def _compute_is_approver(self):
        """
        Kiểm tra user hiện tại có phải Approver (Giám đốc) không.
        Admin sẽ trả về False để thấy được các nút bị ẩn bởi is_approver.
        """
        user = self.env.user
        is_admin = user.has_group("base.group_system")
        is_approver = user.has_group(
            "trasas_contract_management.group_contract_approver"
        )
        for record in self:
            record.is_approver = is_approver and not is_admin

    def _compute_is_operation_user(self):
        """
        Kiểm tra user có thuộc nhóm Vận hành thuần túy không (để hiện nút Xác nhận hoàn tất)
        Ẩn đối với HCNS, BGĐ và GĐ Nghiệp vụ theo yêu cầu.
        """
        user = self.env.user
        is_admin = user.has_group("base.group_system")
        is_user = user.has_group("trasas_contract_management.group_contract_user")
        is_manager = user.has_group("trasas_contract_management.group_contract_manager")
        is_approver = user.has_group(
            "trasas_contract_management.group_contract_approver"
        )
        is_reviewer = user.has_group(
            "trasas_contract_management.group_contract_reviewer"
        )

        for record in self:
            # Hiện cho User nhưng ẩn cho Manager/Approver/Reviewer (dù có inherit)
            # Admin vẫn cho hiện để quản trị
            if is_admin:
                record.is_operation_user = True
            else:
                record.is_operation_user = is_user and not (
                    is_manager or is_approver or is_reviewer
                )

    def _compute_is_cancel_dept_approver(self):
        """Kiểm tra user hiện tại có phải trưởng phòng của người yêu cầu hủy"""
        for record in self:
            if not record.cancel_requester_id:
                record.is_cancel_dept_approver = False
                continue
            # Tìm employee của người yêu cầu hủy
            employee = self.env["hr.employee"].search(
                [("user_id", "=", record.cancel_requester_id.id)], limit=1
            )
            if employee and employee.parent_id and employee.parent_id.user_id:
                record.is_cancel_dept_approver = (
                    employee.parent_id.user_id.id == self.env.user.id
                )
            else:
                # Nếu không tìm được trưởng phòng, cho manager duyệt
                is_admin = self.env.user.has_group("base.group_system")
                record.is_cancel_dept_approver = (
                    self.env.user.has_group(
                        "trasas_contract_management.group_contract_manager"
                    )
                    and not is_admin
                )

    def _compute_is_draft_dept_approver(self):
        """Kiểm tra user hiện tại có phải trưởng phòng của người yêu cầu về nháp"""
        for record in self:
            if not record.draft_requester_id:
                record.is_draft_dept_approver = False
                continue
            # Tìm employee của người yêu cầu về nháp
            employee = self.env["hr.employee"].search(
                [("user_id", "=", record.draft_requester_id.id)], limit=1
            )
            if employee and employee.parent_id and employee.parent_id.user_id:
                record.is_draft_dept_approver = (
                    employee.parent_id.user_id.id == self.env.user.id
                )
            else:
                # Nếu không tìm được trưởng phòng, cho manager duyệt
                is_admin = self.env.user.has_group("base.group_system")
                record.is_draft_dept_approver = (
                    self.env.user.has_group(
                        "trasas_contract_management.group_contract_manager"
                    )
                    and not is_admin
                )

    @api.depends("state", "activity_ids", "reviewer_id", "suggested_reviewer_id")
    def _compute_is_reviewer(self):
        """
        Kiểm tra user hiện tại có phải là người đang được giao rà soát không.
        Dựa trên:
        1. Trạng thái là 'in_review'
        2. Là người được chỉ định trong form (reviewer_id hoặc suggested_reviewer_id)
        3. HOẶC có một Activity 'To Do' giao đích danh (dùng cho uỷ quyền/bàn giao)
        4. HOẶC là Admin/Manager (quyền quản trị)
        """
        current_user_id = self.env.user.id
        todo_type_id = self.env.ref("mail.mail_activity_data_todo").id
        user = self.env.user
        is_admin = user.has_group("base.group_system")

        for record in self:
            if record.state != "in_review":
                record.is_reviewer = False
                continue

            # Kiểm tra xem user hiện tại có phải là người được chỉ định rà soát trên form không
            is_designated = current_user_id in [
                record.reviewer_id.id,
                record.suggested_reviewer_id.id,
            ]

            # Chỉ Admin hoặc Người được chỉ định đích danh mới thấy nút
            if is_admin or is_designated:
                record.is_reviewer = True
                continue

            # Với User khác, phải có activity giao đích danh (trường hợp uỷ quyền rà soát)
            activity = record.activity_ids.filtered(
                lambda a: (
                    a.activity_type_id.id == todo_type_id
                    and a.user_id.id == current_user_id
                    and (
                        "B3" in (a.summary or "")
                        or "rà soát" in (a.summary or "").lower()
                    )
                )
            )
            record.is_reviewer = bool(activity)

    @api.depends("state", "activity_ids")
    def _compute_is_current_approver(self):
        """
        Kiểm tra user hiện tại có phải là người đang được giao phê duyệt không.
        Dựa trên:
        1. Trạng thái là 'waiting'
        2. Có một Activity 'To Do' chưa hoàn thành giao cho user hiện tại.
        3. HOẶC user thuộc nhóm Approver thì thấy nút phê duyệt luôn.
        """
        current_user_id = self.env.user.id
        todo_type_id = self.env.ref("mail.mail_activity_data_todo").id
        user = self.env.user
        is_admin = user.has_group("base.group_system")
        is_approver_group = user.has_group(
            "trasas_contract_management.group_contract_approver"
        )
        is_reviewer_group = user.has_group(
            "trasas_contract_management.group_contract_reviewer"
        )

        for record in self:
            # Ban giám đốc hoặc GĐ Nghiệp vụ được thấy nút phê duyệt của bất kỳ hợp đồng nào đang chờ
            if is_admin or (
                (is_approver_group or is_reviewer_group) and record.state == "waiting"
            ):
                record.is_current_approver = True
                continue

            if record.state != "waiting":
                record.is_current_approver = False
                continue

            # Fallback activity check
            activity = record.activity_ids.filtered(
                lambda a: (
                    a.activity_type_id.id == todo_type_id
                    and a.user_id.id == current_user_id
                    and (
                        "B4" in (a.summary or "")
                        or "phê duyệt" in (a.summary or "").lower()
                    )
                )
            )
            record.is_current_approver = bool(activity)

    @api.depends("date_start", "date_end")
    def _compute_duration_days(self):
        """Tính số ngày hiệu lực"""
        for record in self:
            if record.date_start and record.date_end:
                delta = record.date_end - record.date_start
                record.duration_days = delta.days + 1
            else:
                record.duration_days = 0

    @api.depends("date_end")
    def _compute_days_to_expire(self):
        """Tính số ngày còn lại đến khi hết hạn"""
        today = fields.Date.context_today(self)
        for record in self:
            if record.date_end:
                delta = record.date_end - today
                record.days_to_expire = delta.days
            else:
                record.days_to_expire = 0

    # ============ ONCHANGE ============
    @api.onchange("contract_type_id")
    def _onchange_contract_type_id(self):
        """Tự động điền thời hạn mặc định khi chọn loại hợp đồng"""
        if self.contract_type_id and self.contract_type_id.default_duration_days:
            if self.date_start:
                self.date_end = self.date_start + timedelta(
                    days=self.contract_type_id.default_duration_days - 1
                )

    @api.onchange("date_start")
    def _onchange_date_start(self):
        """Tự động cập nhật date_end khi thay đổi date_start"""
        if (
            self.date_start
            and self.contract_type_id
            and self.contract_type_id.default_duration_days
        ):
            if not self.date_end or self.date_end < self.date_start:
                self.date_end = self.date_start + timedelta(
                    days=self.contract_type_id.default_duration_days - 1
                )

    @api.onchange("contract_date")
    def _onchange_contract_date(self):
        """
        Tự động tính hạn ký (sign_deadline) = Ngày tạo (contract_date) + 7 ngày
        """
        if self.contract_date:
            self.sign_deadline = self.contract_date + timedelta(days=7)

    # ============ COMPUTE METHODS (SIGN) ============
    @api.depends("sign_request_ids")
    def _compute_sign_request_count(self):
        for record in self:
            record.sign_request_count = len(record.sign_request_ids)

    # ============ CONSTRAINTS ============
    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        """Kiểm tra ngày bắt đầu phải trước ngày kết thúc"""
        for record in self:
            if record.date_start and record.date_end:
                if record.date_start > record.date_end:
                    raise ValidationError(_("Ngày bắt đầu phải trước ngày kết thúc!"))

    @api.constrains("state")
    def _check_signing_flow_completion(self):
        """
        [B9-B13] Kiểm tra luồng ký phải hoàn tất đúng quy trình
        Trước khi signed, cả 2 bên phải ký
        """
        for record in self:
            if record.state == "signed":
                # Validate: Phải có TRASAS ký và File scan
                if not record.internal_sign_date:
                    raise ValidationError(
                        _("Lỗi! TRASAS chưa ký. Hãy bấm 'Xác nhận TRASAS đã ký' trước.")
                    )
                if not record.final_scan_file:
                    raise ValidationError(_("Lỗi! Chưa upload bản scan hoàn tất."))

    # ============ CREATE & WRITE ============
    @api.model_create_multi
    def create(self, vals_list):
        """Tạo số hợp đồng tự động"""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                contract_type = self.env["trasas.contract.type"].browse(
                    vals.get("contract_type_id")
                )
                if contract_type and contract_type.name_pattern:
                    # Sử dụng pattern từ loại hợp đồng
                    vals["name"] = self._generate_contract_number(contract_type)
                else:
                    # Sequence mặc định
                    vals["name"] = (
                        self.env["ir.sequence"].next_by_code("trasas.contract") or "New"
                    )
        records = super().create(vals_list)
        records._create_document_folder()
        return records

    def write(self, vals):
        res = super().write(vals)

        # Cập nhật tên thư mục nếu name (số hợp đồng) đổi
        if "name" in vals:
            for rec in self:
                if rec.document_folder_id:
                    folder_name = (
                        f"{rec.name}_{rec.partner_id.name}"
                        if rec.name
                        else rec.partner_id.name
                    )
                    rec.document_folder_id.sudo().write({"name": folder_name})

        # Xử lý khi có file mới tải lên => sync sang Documents app
        if any(f in vals for f in ["final_scan_file", "stamped_file"]):
            for rec in self:
                if vals.get("final_scan_file"):
                    rec._create_attachment_from_binary(
                        vals.get("final_scan_file"),
                        vals.get("final_scan_filename") or f"Ban_Scan_{rec.name}.pdf",
                    )
                if vals.get("stamped_file"):
                    rec._create_attachment_from_binary(
                        vals.get("stamped_file"),
                        vals.get("stamped_filename") or f"Ban_Dong_Dau_{rec.name}.pdf",
                    )
                rec._sync_attachments_to_document()

        return res

    def message_post(self, **kwargs):
        """Override để đồng bộ file ngay khi upload qua chatter"""
        msg = super().message_post(**kwargs)
        if msg.attachment_ids:
            self._sync_attachments_to_document()
        return msg

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
        for rec in self:
            # Nếu folder đã có nhưng bị lưu trữ (archived), thì khôi phục lại
            if rec.document_folder_id and not rec.document_folder_id.active:
                rec.document_folder_id.write({"active": True})
                continue

            if (
                not rec.document_folder_id
                and rec.contract_type_id
                and rec.contract_type_id.document_folder_id
            ):
                folder_name = (
                    f"{rec.name}_{rec.partner_id.name}"
                    if rec.name
                    else rec.partner_id.name
                )
                folder = Document.create(
                    {
                        "name": folder_name,
                        "type": "folder",
                        "folder_id": rec.contract_type_id.document_folder_id.id,
                    }
                )
                rec.write({"document_folder_id": folder.id})

    @api.model
    def _create_folders_for_existing(self):
        # 1. Tạo folder cho những thằng chưa có
        records_no_folder = self.search([("document_folder_id", "=", False)])
        records_no_folder._create_document_folder()

        # 2. Đồng bộ file cho TOÀN BỘ hợp đồng (chỉ những thằng folder đang active)
        # Search lại để lấy danh sách mới nhất sau Step 1
        all_contracts = self.search([("document_folder_id", "!=", False)])
        for rec in all_contracts:
            # Skip nếu folder vẫn archived (trường hợp hiếm)
            if not rec.document_folder_id.active:
                continue

            # Tạo attachment cho các trường binary nếu đã có dữ liệu nhưng chưa có attachment
            if rec.final_scan_file:
                rec._create_attachment_from_binary(
                    rec.final_scan_file,
                    rec.final_scan_filename or f"Ban_Scan_{rec.name}.pdf",
                )
            if rec.stamped_file:
                rec._create_attachment_from_binary(
                    rec.stamped_file,
                    rec.stamped_filename or f"Ban_Dong_Dau_{rec.name}.pdf",
                )
            rec._sync_attachments_to_document()

    def _sync_attachments_to_document(self):
        """Đồng bộ các file đính kèm của Hợp đồng sang ứng dụng Documents.
        Bao gồm cả Chatter và các trường Binary (final_scan_file, stamped_file).
        """
        self.ensure_one()
        if not self.document_folder_id or not self.document_folder_id.active:
            return

        Document = self.env["documents.document"].sudo()
        Attachment = self.env["ir.attachment"].sudo()

        # Tìm toàn bộ attachment liên quan (cả chatter và binary field)
        domain = [
            ("res_model", "=", self._name),
            ("res_id", "=", self.id),
        ]
        attachments = Attachment.search(domain)

        for attachment in attachments:
            # Kiểm tra xem đã tồn tại doc cho attachment này chưa
            existing = Document.search([("attachment_id", "=", attachment.id)], limit=1)
            if not existing:
                Document.create(
                    {
                        "attachment_id": attachment.id,
                        "folder_id": self.document_folder_id.id,
                        "name": attachment.name,
                    }
                )

    def action_view_documents(self):
        """Mở danh sách file đính kèm của Hợp đồng (Giao diện list view)"""
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

    def _generate_contract_number(self, contract_type):
        """Tạo số hợp đồng theo pattern"""
        # Đếm số hợp đồng cùng loại trong năm
        year = fields.Date.context_today(self).year
        count = (
            self.search_count(
                [
                    ("contract_type_id", "=", contract_type.id),
                    ("create_date", ">=", f"{year}-01-01"),
                    ("create_date", "<=", f"{year}-12-31"),
                ]
            )
            + 1
        )

        # Format theo pattern
        pattern = contract_type.name_pattern or "{code}/{year}/{sequence:04d}"
        return pattern.format(code=contract_type.code, year=year, sequence=count)

    # ============ STATE WORKFLOW ACTIONS ============
    def action_submit_for_approval(self):
        """Gửi duyệt (Draft → Waiting)"""
        for record in self:
            if record.state != "draft":
                raise UserError(_("Chỉ có thể gửi duyệt hợp đồng ở trạng thái Nháp!"))

            # Kiểm tra file đính kèm trước khi gửi duyệt
            attachment_count = self.env["ir.attachment"].search_count(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", record.id),
                ]
            )
            if attachment_count == 0:
                raise UserError(
                    _(
                        "Vui lòng đính kèm ít nhất một file hợp đồng trước khi gửi duyệt!"
                    )
                )

            record.write({"state": "waiting"})

            # Gửi email thông báo cho người phê duyệt
            record._send_approval_notification()

            # --- Activity Logic ---
            record._close_activities()

            # Tạo Activity cho Người phê duyệt đề xuất hoặc Nhóm Approver (Giám đốc)
            approver_user = record.suggested_approver_id
            if not approver_user:
                approvers = record._get_users_from_group(
                    "trasas_contract_management.group_contract_approver"
                )
                if approvers:
                    approver_user = approvers[0]

            if approver_user:
                record._schedule_activity(
                    approver_user.id,
                    _("⏳ Yêu cầu phê duyệt hợp đồng: %s") % record.name,
                    deadline=1,
                    note="Yêu cầu phê duyệt hợp đồng",
                )

            record.message_post(
                body=_("Hợp đồng đã được gửi để phê duyệt."),
                subject=_("Gửi duyệt hợp đồng"),
            )

    # ============ ACTIVITY HELPERS ============
    def _get_users_from_group(self, group_xmlid):
        """
        Lấy danh sách users thuộc một security group

        Args:
            group_xmlid (str): XML ID của group (vd: 'trasas_contract_management.group_contract_approver')

        Returns:
            res.users: Recordset của users thuộc group (chỉ active users)
        """
        try:
            group = self.env.ref(group_xmlid)
        except ValueError:
            # Group không tồn tại
            return self.env["res.users"]

        # Lấy users từ group (tương thích Odoo 19)
        # group.user_ids trả về danh sách users thuộc group
        return group.user_ids.filtered(lambda u: u.active)

    def _schedule_activity(self, user_id, summary, deadline=0, note=False):
        """Tạo công việc (Activity) mới với note để track loại bước"""
        if not user_id:
            return
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            user_id=user_id,
            summary=summary,
            note=note or "",
            date_deadline=fields.Date.context_today(self) + timedelta(days=deadline),
        )

    def _close_activities(self):
        """Đóng tất cả công việc cũ"""
        self.activity_feedback(["mail.mail_activity_data_todo"])

    def activity_feedback(self, act_type_xmlids, user_id=False, feedback=False):
        """
        Override để xử lý khi Activity được mark done.
        Tự động chuyển sang bước tiếp theo trong luồng ký.
        """
        # Lấy activities trước khi đóng để biết loại bước
        for record in self:
            if record.state != "signing":
                continue

            activities = record.activity_ids.filtered(
                lambda a: (
                    a.activity_type_id.id
                    == self.env.ref("mail.mail_activity_data_todo").id
                    and (not user_id or a.user_id.id == user_id)
                )
            )

            for activity in activities:
                summary = activity.summary or ""
                note = activity.note or ""

                # [B12] Đã gửi cho đối tác → Tạo B13
                if "B12" in summary or "B12" in note:
                    # Gọi action và tạo activity tiếp theo
                    record._handle_b12_done()

                # [B13] Đã nhận từ đối tác → Kiểm tra file scan và hoàn tất
                elif "B13" in summary or "B13" in note:
                    record._handle_b13_done()

        # Gọi super để thực sự đóng activity
        return super().activity_feedback(
            act_type_xmlids, user_id=user_id, feedback=feedback
        )

    def _handle_b12_done(self):
        """Xử lý khi Activity B12 (Đã gửi đối tác) được mark done"""
        self.ensure_one()
        if self.signing_flow != "trasas_first":
            return

        # Cập nhật ngày gửi
        self.write({"sent_to_partner_date": fields.Date.context_today(self)})
        self.message_post(
            body=_("📤 [B12] Đã gửi hợp đồng cho đối tác/khách hàng ký (Luồng A)")
        )

        # Tạo Activity B13
        self._schedule_activity(
            self.user_id.id,
            _("📥 Nhận hợp đồng từ đối tác (B13): %s") % self.name,
            deadline=7,
            note="B13 - Cần upload bản scan trước khi mark done",
        )

    def _handle_b13_done(self):
        """Xử lý khi Activity B13 (Đã nhận từ đối tác) được mark done"""
        self.ensure_one()

        # Kiểm tra file scan
        if not self.final_scan_file:
            raise UserError(
                _(
                    "Vui lòng upload bản scan hợp đồng trước khi hoàn tất!\n"
                    "Vào tab 'File đính kèm' để upload file."
                )
            )

        self.message_post(
            body=_("[B13] Nhận lại hợp đồng đã ký đầy đủ từ cả hai phía (Luồng A)")
        )

        # Hoàn tất ký kết
        self._complete_signing()

    def _complete_signing(self):
        """
        Hoàn tất ký kết (Signing → Signed)
        Được gọi từ activity workflow hoặc button
        """
        self.ensure_one()

        if self.state != "signing":
            return

        # Validate: TRASAS đã ký và có file scan
        if not self.internal_sign_date:
            raise UserError(_("TRASAS chưa ký hợp đồng!"))

        if not self.final_scan_file:
            raise UserError(
                _(
                    "Vui lòng upload bản scan hợp đồng đã ký đầy đủ!\n"
                    "Vào tab 'File đính kèm' để upload file."
                )
            )

        self.write(
            {
                "state": "signed",
                "signed_date": fields.Date.context_today(self),
            }
        )

        self.message_post(
            body=_("Hoàn tất ký kết - Hợp đồng đã được ký đầy đủ bởi cả hai phía."),
            subject=_("Hoàn tất ký kết"),
        )

        # Thông báo cho HCNS để đóng dấu
        self._send_seal_notification()

        # [B16-B18] Gửi cho TẤT CẢ HCNS (nhóm Contract Manager) để đóng dấu/lưu kho
        managers = self._get_users_from_group(
            "trasas_contract_management.group_contract_manager"
        )
        for manager in managers:
            self._schedule_activity(
                manager.id,
                _("Đóng dấu & Lưu kho hợp đồng (B16-B18): %s") % self.name,
                deadline=1,
                note="Đóng dấu & Lưu kho",
            )

    def action_submit_for_review(self):
        """
        [B3] Gửi rà soát (Draft → In Review)
        Lấy ý kiến nội bộ, chỉnh sửa và hoàn thiện nội dung
        """
        for record in self:
            if record.state != "draft":
                raise UserError(_("Chỉ có thể gửi rà soát hợp đồng ở trạng thái Nháp!"))

            # Kiểm tra file đính kèm (ir.attachment) trước khi gửi rà soát
            attachment_count = self.env["ir.attachment"].search_count(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", record.id),
                ]
            )
            if attachment_count == 0:
                raise UserError(
                    _("Vui lòng đính kèm ít nhất một file trước khi gửi rà soát!")
                )

            record.write({"state": "in_review"})
            record.message_post(
                body=_(
                    "📋 [B3] Gửi rà soát - Lấy ý kiến nội bộ để chỉnh sửa và hoàn thiện nội dung."
                ),
                subject=_("Gửi rà soát"),
            )

            # --- Activity Logic ---
            record._close_activities()

            # [B3] Tạo Activity cho Người rà soát đề xuất (Bắt buộc)
            reviewer = record.suggested_reviewer_id
            if not reviewer:
                raise UserError(
                    _("Vui lòng chọn Người rà soát đề xuất trước khi gửi rà soát!")
                )

            # Tạo Activity rà soát
            record._schedule_activity(
                reviewer.id,
                _("Rà soát hợp đồng: %s (B3)") % record.name,
                deadline=1,
                note="Vui lòng rà soát hợp đồng",
            )

            # Gửi email yêu cầu rà soát
            template = self.env.ref(
                "trasas_contract_management.email_template_contract_review_request",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

    def action_confirm_review(self):
        """
        [B3] Xác nhận rà soát xong (In Review → Waiting)
        Trưởng bộ phận/Pháp chế xác nhận hoàn tất rà soát
        """
        for record in self:
            if record.state != "in_review":
                raise UserError(_("Hợp đồng chưa ở trạng thái rà soát!"))

            # Ghi lại ngay để chắc chắn lưu
            record.write(
                {
                    "state": "waiting",
                    "reviewer_id": self.env.user.id,
                    "review_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_("[B3] Hoàn tất rà soát - Trình Giám đốc phê duyệt."),
                subject=_("Hoàn tất rà soát"),
            )

            # --- Activity Logic ---
            record._close_activities()

            # [B4] Gửi cho Giám đốc - Ưu tiên người duyệt đề xuất
            approver_user = record.suggested_approver_id
            if not approver_user:
                approvers = record._get_users_from_group(
                    "trasas_contract_management.group_contract_approver"
                )
                if approvers:
                    approver_user = approvers[0]

            if approver_user:
                record._schedule_activity(
                    approver_user.id,
                    _("⏳ Yêu cầu phê duyệt hợp đồng: %s (B4)") % record.name,
                    deadline=2,  # +2 ngày
                )

        # Trả về action để refresh form
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def action_approve(self):
        """
        [B4-B5] Phê duyệt (Waiting → Approved)
        Ban Giám đốc phê duyệt hợp đồng
        """
        if not self.env.user.has_group(
            "trasas_contract_management.group_contract_approver"
        ):
            raise UserError(_("Bạn không có quyền phê duyệt hợp đồng!"))

        for record in self:
            if record.state != "waiting":
                raise UserError(_("Chỉ có thể phê duyệt hợp đồng đang chờ duyệt!"))

            record.write(
                {
                    "state": "approved",
                    "approver_id": self.env.user.id,
                    "approved_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "[B5] Phê duyệt - Hợp đồng đã được phê duyệt bởi %s. Sắp bắt đầu ký kết."
                )
                % self.env.user.name,
                subject=_("Phê duyệt hợp đồng"),
            )

            # Thông báo cho người tạo
            record._send_approved_notification()

            # --- Activity Logic ---
            record._close_activities()

            # [B6] Giao lại việc cho người tạo để đi ký
            record._schedule_activity(
                record.user_id.id,
                _("Bắt đầu quy trình ký: %s (B6)") % record.name,
                deadline=2,  # +2 ngày
                note="Bắt đầu quy trình ký",
            )

    def action_reject(self):
        """
        [B5] Từ chối (Waiting → Draft)
        Ban Giám đốc từ chối hợp đồng, quay về B1 để sửa
        """
        if not self.env.user.has_group(
            "trasas_contract_management.group_contract_approver"
        ):
            raise UserError(_("Bạn không có quyền từ chối hợp đồng!"))

        self.ensure_one()
        if self.state != "waiting":
            raise UserError(_("Chỉ có thể từ chối hợp đồng đang chờ duyệt!"))

        # Mở wizard để nhập lý do từ chối
        return {
            "name": _("Từ chối Hợp đồng"),
            "type": "ir.actions.act_window",
            "res_model": "trasas.contract.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_contract_id": self.id,
            },
        }

    def action_confirm_rejection(self, reason):
        """
        [B5] Xác nhận từ chối với lý do
        """
        self.ensure_one()
        self.write(
            {
                "state": "draft",
                "rejection_reason": reason,
            }
        )

        self.message_post(
            body=_("[B5] Từ chối - Hợp đồng bị từ chối bởi %s.<br/>Lý do: %s")
            % (self.env.user.name, reason),
            subject=_("Từ chối hợp đồng"),
        )

        # Thông báo cho người tạo
        self._send_rejected_notification()

        # --- Activity Logic ---
        self._close_activities()
        self._schedule_activity(
            self.user_id.id,
            _("Bị từ chối. Vui lòng kiểm tra và sửa lại: %s") % self.name,
            deadline=0,  # Hôm nay
            note="Sửa lại hợp đồng theo comment",
        )

    def action_start_signing(self):
        """
        [B6-B9] Bắt đầu ký & Phân loại luồng ký
        - B6: Khởi tạo luồng ký (AI/Odoo Sign)
        - B9: Phân loại theo: TRASAS ký trước hay Đối tác ký trước

        Trạng thái: Approved → Signing
        """
        for record in self:
            if record.state != "approved":
                raise UserError(_("Chỉ có thể bắt đầu ký hợp đồng đã được phê duyệt!"))

            record.write({"state": "signing"})

            flow_name = dict(record._fields["signing_flow"].selection).get(
                record.signing_flow
            )
            record.message_post(
                body=_(
                    "🖊️ [B6-B9] Bắt đầu ký kết hợp đồng.<br/>Luồng ký: <strong>%s</strong>"
                )
                % flow_name,
                subject=_("Bắt đầu ký kết"),
            )

            # --- Activity Logic ---
            record._close_activities()

            # [B10/B14] Tạo Activity theo luồng ký
            if record.signing_flow == "trasas_first":
                # Luồng A: TRASAS ký trước [B11]
                # Ưu tiên Người phê duyệt đề xuất
                approver_user = record.suggested_approver_id
                if not approver_user:
                    approvers = record._get_users_from_group(
                        "trasas_contract_management.group_contract_approver"
                    )
                    if approvers:
                        approver_user = approvers[0]

                if approver_user:
                    record._schedule_activity(
                        approver_user.id,
                        _("🖊️ Ký hợp đồng TRASAS trước (B11): %s") % record.name,
                        deadline=2,  # +2 ngày
                        note="Ký hợp đồng TRASAS trước",
                    )
            else:
                # Luồng B: Đối tác ký trước [B14]
                # Giao cho người tạo (vận hành) chờ đối tác ký
                record._schedule_activity(
                    record.user_id.id,
                    _("Chờ đối tác ký hợp đồng (B14): %s") % record.name,
                    deadline=5,  # +5 ngày
                    note="Chờ đối tác ký hợp đồng",
                )

    def action_mark_internal_signed(self):
        """
        [B11 hoặc B15] Xác nhận TRASAS đã ký

        - B11: Luồng A (TRASAS ký trước)
        - B15: Luồng B (Đối tác ký trước)
        """
        for record in self:
            record.write({"internal_sign_date": fields.Datetime.now()})

            if record.signing_flow == "trasas_first":
                msg = "[B11] TRASAS đã ký hợp đồng (Luồng A - TRASAS ký trước)"
            else:
                msg = "[B15] TRASAS đã ký hợp đồng (Luồng B - Đối tác ký trước)"

            record.message_post(body=_(msg))

            # [B12 hoặc completion] Tạo Activity cho bước tiếp theo
            if record.signing_flow == "trasas_first":
                # Luồng A: Tiếp theo là gửi cho đối tác [B12]
                record._close_activities()
                record._schedule_activity(
                    record.user_id.id,
                    _("📤 Xác nhận đã gửi hợp đồng cho đối tác (B12): %s")
                    % record.name,
                    deadline=1,
                    note="Gửi hợp đồng cho đối tác",
                )
            else:
                # Luồng B: Tiếp theo là Kiểm tra & Hoàn tất [B13]
                record._close_activities()
                record._schedule_activity(
                    record.user_id.id,
                    _("Kiểm tra & Hoàn tất (B13): %s") % record.name,
                    deadline=1,
                    note="Kiểm tra & Hoàn tất",
                )

    def action_mark_sent_to_partner(self):
        """
        [B12] Xác nhận đã gửi cho đối tác (Luồng A)
        Gửi hợp đồng cho đối tác/khách hàng để ký
        """

        for record in self:
            if record.signing_flow != "trasas_first":
                raise UserError(_("Chỉ dùng cho luồng TRASAS ký trước!"))

            record.write({"sent_to_partner_date": fields.Date.context_today(record)})
            record.message_post(
                body=_("[B12] Đã gửi hợp đồng cho đối tác/khách hàng ký (Luồng A)")
            )

            # [B13] Tiếp theo: Chờ đối tác ký và gửi lại
            record._close_activities()
            record._schedule_activity(
                record.user_id.id,
                _("Theo dõi & Nhận lại hợp đồng (B13): %s") % record.name,
                deadline=7,  # +7 ngày
                note="Theo dõi & Nhận lại hợp đồng",
            )

        # Nếu chỉ có 1 bản ghi, mở cửa sổ soạn mail
        if len(self) == 1:
            return self.action_send_contract_to_partner()

    def action_send_contract_to_partner(self):
        """Mở wizard gửi email cho đối tác kèm file hợp đồng"""
        self.ensure_one()

        # Tìm template
        template = self.env.ref(
            "trasas_contract_management.email_template_contract_send_to_partner",
            raise_if_not_found=False,
        )

        compose_form = self.env.ref(
            "mail.email_compose_message_wizard_form", raise_if_not_found=False
        )

        ctx = {
            "default_model": "trasas.contract",
            "default_res_ids": [self.id],
            "default_template_id": template.id if template else False,
            "default_composition_mode": "comment",
            "mark_so_as_sent": True,
            "force_email": True,
        }

        return {
            "name": _("Gửi hợp đồng cho đối tác"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }

    def action_mark_partner_signed(self):
        """
        [B13 hoặc B14] Xác nhận đối tác đã ký

        - B13: Luồng A (Nhận lại sau khi TRASAS & đối tác ký)
        - B14: Luồng B (Nhận hợp đồng đã ký từ đối tác)
        """
        for record in self:
            record.write({"partner_sign_date": fields.Date.context_today(record)})

            if record.signing_flow == "trasas_first":
                msg = "[B13] Nhận lại hợp đồng đã ký đầy đủ từ cả hai phía (Luồng A)"
            else:
                msg = "[B14] Nhận hợp đồng đã ký từ đối tác (Luồng B)"

            record.message_post(body=_(msg))

            # Luồng B: Tiếp theo là Giám đốc ký [B15]
            if record.signing_flow == "partner_first":
                record._close_activities()
                # Ưu tiên Người phê duyệt đề xuất
                approver_user = record.suggested_approver_id
                if not approver_user:
                    approvers = record._get_users_from_group(
                        "trasas_contract_management.group_contract_approver"
                    )
                    if approvers:
                        approver_user = approvers[0]

                if approver_user:
                    # Tạo activity cho giám đốc
                    record._schedule_activity(
                        approver_user.id,
                        _("Ký hợp đồng (đã có chữ ký đối tác) (B15): %s") % record.name,
                        deadline=2,
                        note="Ký hợp đồng (đã có chữ ký đối tác)",
                    )
                    # Gửi email yêu cầu ký
                    template = self.env.ref(
                        "trasas_contract_management.email_template_contract_sign_request_partner_signed",
                        raise_if_not_found=False,
                    )
                    if template:
                        # Gửi cho giám đốc
                        template.send_mail(record.id, force_send=True)

    def action_confirm_signed(self):
        """
        [B13] Xác nhận đã ký hoàn tất (Signing → Signed)
        Button wrapper - gọi _complete_signing
        """
        for record in self:
            record._complete_signing()

    def action_archive_contract(self):
        """
        Xác nhận đã đóng dấu và lưu kho (Signed → Archived)
        """
        for record in self:
            if record.state != "signed":
                raise UserError(_("Chỉ có thể lưu kho hợp đồng đã ký!"))

            record.write({"state": "archived"})

            record.message_post(
                body=_("📦 Hợp đồng đã được đóng dấu và lưu kho bởi %s.")
                % self.env.user.name,
                subject=_("Lưu kho hợp đồng"),
            )

            record._close_activities()

    def action_cancel(self):
        """Hủy hợp đồng (chỉ cho trạng thái trước khi duyệt)"""
        for record in self:
            if record.state in ["approved", "signing", "signed", "archived", "expired"]:
                raise UserError(
                    _(
                        "Hợp đồng đã được duyệt! Vui lòng dùng nút 'Yêu cầu hủy' để tạo yêu cầu hủy có phê duyệt."
                    )
                )
            record.write({"state": "cancel"})
            record._close_activities()

            record.message_post(
                body=_("Hợp đồng đã bị hủy bởi %s.") % self.env.user.name,
                subject=_("Hủy hợp đồng"),
            )

    def action_set_to_draft(self):
        """Đặt về nháp (chỉ cho trạng thái in_review, waiting)"""
        for record in self:
            if record.state in ["approved", "signing", "signed", "archived"]:
                raise UserError(
                    _(
                        "Hợp đồng đã được duyệt! Vui lòng dùng nút 'Yêu cầu về nháp' để tạo yêu cầu có phê duyệt."
                    )
                )
            record.write(
                {
                    "state": "draft",
                    "approver_id": False,
                    "approved_date": False,
                    "reviewer_id": False,
                    "review_date": False,
                    "internal_sign_date": False,
                }
            )
            record._close_activities()

            record.message_post(
                body=_("Hợp đồng đã được đặt về trạng thái Nháp."),
                subject=_("Đặt về nháp"),
            )

    # ============ CANCEL REQUEST WORKFLOW ============
    def action_request_cancel(self):
        """Yêu cầu hủy hợp đồng (mở wizard nhập lý do)"""
        self.ensure_one()
        if self.state not in ["approved", "signing", "signed", "archived"]:
            raise UserError(_("Chỉ có thể yêu cầu hủy hợp đồng đã được duyệt!"))

        return {
            "name": _("Yêu cầu hủy Hợp đồng"),
            "type": "ir.actions.act_window",
            "res_model": "trasas.contract.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_contract_id": self.id,
            },
        }

    def _submit_cancel_request(self, reason):
        """Gửi yêu cầu hủy (được gọi từ wizard)"""
        self.ensure_one()

        # Tìm trưởng phòng của người yêu cầu
        employee = self.env["hr.employee"].search(
            [("user_id", "=", self.env.user.id)], limit=1
        )
        dept_manager = False
        if employee and employee.parent_id and employee.parent_id.user_id:
            dept_manager = employee.parent_id.user_id

        # Nếu không tìm thấy trưởng phòng, dùng manager group
        if not dept_manager:
            managers = self._get_users_from_group(
                "trasas_contract_management.group_contract_manager"
            )
            if managers:
                dept_manager = managers[0]

        self.write(
            {
                "cancel_request_state": "dept_pending",
                "cancel_reason": reason,
                "cancel_requester_id": self.env.user.id,
                "cancel_dept_approver_id": False,
                "cancel_bgd_approver_id": False,
            }
        )

        self.message_post(
            body=_(
                "📋 Yêu cầu hủy hợp đồng bởi %s.<br/>Lý do: %s<br/>Chờ Trưởng phòng duyệt."
            )
            % (self.env.user.name, reason),
            subject=_("Yêu cầu hủy hợp đồng"),
        )

        # Gửi Activity cho trưởng phòng
        if dept_manager:
            self._schedule_activity(
                dept_manager.id,
                _("⚠️ Duyệt yêu cầu hủy hợp đồng: %s") % self.name,
                deadline=1,
                note="Yêu cầu hủy hợp đồng - Cần Trưởng phòng duyệt",
            )

    def action_approve_cancel_dept(self):
        """Trưởng phòng duyệt yêu cầu hủy → chuyển sang chờ BGĐ"""
        for record in self:
            if record.cancel_request_state != "dept_pending":
                raise UserError(_("Không có yêu cầu hủy đang chờ Trưởng phòng duyệt!"))

            record.write(
                {
                    "cancel_request_state": "bgd_pending",
                    "cancel_dept_approver_id": self.env.user.id,
                }
            )

            record._close_activities()

            record.message_post(
                body=_(
                    "✅ Trưởng phòng %s đã duyệt yêu cầu hủy. Chuyển sang chờ Ban Giám đốc."
                )
                % self.env.user.name,
                subject=_("Trưởng phòng duyệt hủy"),
            )

            # Gửi Activity cho Ban Giám đốc (Ưu tiên người đã duyệt hợp đồng này)
            approver_user = record.approver_id
            if not approver_user:
                approvers = record._get_users_from_group(
                    "trasas_contract_management.group_contract_approver"
                )
                if approvers:
                    approver_user = approvers[0]

            if approver_user:
                record._schedule_activity(
                    approver_user.id,
                    _("⚠️ Duyệt yêu cầu hủy hợp đồng (BGĐ): %s") % record.name,
                    deadline=1,
                    note="Yêu cầu hủy hợp đồng - Cần Ban Giám đốc duyệt",
                )

    def action_approve_cancel_bgd(self):
        """Ban Giám đốc duyệt yêu cầu hủy → thực hiện hủy"""
        if not self.env.user.has_group(
            "trasas_contract_management.group_contract_approver"
        ):
            raise UserError(_("Chỉ Ban Giám đốc mới có quyền duyệt hủy!"))

        for record in self:
            if record.cancel_request_state != "bgd_pending":
                raise UserError(_("Không có yêu cầu hủy đang chờ Ban Giám đốc duyệt!"))

            record.write(
                {
                    "cancel_request_state": "approved",
                    "cancel_bgd_approver_id": self.env.user.id,
                    "state": "cancel",
                }
            )

            record._close_activities()

            record.message_post(
                body=_(
                    "✅ Ban Giám đốc %s đã duyệt yêu cầu hủy.<br/>"
                    "Lý do hủy: %s<br/>"
                    "Hợp đồng đã được hủy."
                )
                % (self.env.user.name, record.cancel_reason),
                subject=_("Hợp đồng đã bị hủy"),
            )

    def action_reject_cancel(self):
        """Từ chối yêu cầu hủy"""
        for record in self:
            if record.cancel_request_state not in ["dept_pending", "bgd_pending"]:
                raise UserError(_("Không có yêu cầu hủy đang chờ duyệt!"))

            old_state = record.cancel_request_state
            record.write(
                {
                    "cancel_request_state": "rejected",
                }
            )

            record._close_activities()

            level = "Trưởng phòng" if old_state == "dept_pending" else "Ban Giám đốc"
        record.message_post(
            body=_("❌ %s %s đã từ chối yêu cầu hủy hợp đồng.")
            % (level, self.env.user.name),
            subject=_("Từ chối hủy hợp đồng"),
        )

    # ==========================================
    # LUỒNG PHÊ DUYỆT ĐẶT VỀ NHÁP
    # ==========================================
    def action_request_draft(self):
        """Yêu cầu đặt về nháp hợp đồng (mở wizard nhập lý do)"""
        self.ensure_one()
        if self.state not in ["approved", "signing", "signed", "archived"]:
            raise UserError(_("Chỉ có thể yêu cầu về nháp hợp đồng đã được duyệt!"))

        return {
            "name": _("Yêu cầu đưa Hợp đồng về nháp"),
            "type": "ir.actions.act_window",
            "res_model": "trasas.contract.draft.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_contract_id": self.id,
            },
        }

    def _submit_draft_request(self, reason):
        """Được gọi từ wizard: Bắt đầu luồng duyệt đưa về nháp"""
        self.ensure_one()

        # Lấy employee manager/trưởng phòng nếu có
        employee = self.env["hr.employee"].search(
            [("user_id", "=", self.env.user.id)], limit=1
        )
        dept_manager = False
        if employee and employee.parent_id and employee.parent_id.user_id:
            dept_manager = employee.parent_id.user_id

        # Nếu không có nhóm trưởng thì gửi manager
        if not dept_manager:
            managers = self._get_users_from_group(
                "trasas_contract_management.group_contract_manager"
            )
            if managers:
                dept_manager = managers[0]

        self.write(
            {
                "draft_request_state": "dept_pending",
                "draft_reason": reason,
                "draft_requester_id": self.env.user.id,
                "draft_dept_approver_id": False,
                "draft_bgd_approver_id": False,
            }
        )

        self.message_post(
            body=_(
                "📋 Yêu cầu đưa hợp đồng về nháp bởi %s.<br/>Lý do: %s<br/>Chờ Trưởng phòng duyệt."
            )
            % (self.env.user.name, reason),
            subject=_("Yêu cầu đưa về nháp"),
        )

        if dept_manager:
            self._schedule_activity(
                dept_manager.id,
                _("⚠️ Duyệt yêu cầu về nháp (Trưởng phòng): %s") % self.name,
                deadline=1,
                note="Nhân viên yêu cầu đưa hợp đồng về nháp - Cần Trưởng phòng duyệt",
            )

    def action_approve_draft_dept(self):
        """Trưởng phòng duyệt đưa về nháp"""
        for record in self:
            if record.draft_request_state != "dept_pending":
                raise UserError(_("Yêu cầu này không ở trạng thái Chờ Trưởng phòng!"))

            record.write(
                {
                    "draft_request_state": "bgd_pending",
                    "draft_dept_approver_id": self.env.user.id,
                }
            )
            record._close_activities()

            record.message_post(
                body=_(
                    "Trưởng phòng %s đã duyệt yêu cầu đưa về nháp. Chuyển sang chờ Ban Giám đốc duyệt."
                )
                % self.env.user.name,
                subject=_("Trưởng phòng Duyệt về nháp"),
            )

            # Gửi Activity cho Ban Giám đốc (Ưu tiên người đã duyệt hợp đồng này)
            approver_user = record.approver_id
            if not approver_user:
                approvers = record._get_users_from_group(
                    "trasas_contract_management.group_contract_approver"
                )
                if approvers:
                    approver_user = approvers[0]

            if approver_user:
                record._schedule_activity(
                    approver_user.id,
                    _("Duyệt yêu cầu đưa hợp đồng về nháp (BGĐ): %s") % record.name,
                    deadline=1,
                    note="Yêu cầu đưa hợp đồng về nháp - Cần Ban Giám đốc duyệt",
                )

    def action_approve_draft_bgd(self):
        """Ban Giám đốc duyệt đưa về nháp (Thực hiện đặt về nháp)"""
        for record in self:
            if record.draft_request_state != "bgd_pending":
                raise UserError(_("Yêu cầu này không ở trạng thái Chờ Ban Giám đốc!"))

            # Đặt hợp đồng về nháp (xóa bớt các field đã duyệt)
            record.write(
                {
                    "state": "draft",
                    "draft_request_state": "approved",
                    "draft_bgd_approver_id": self.env.user.id,
                    "approver_id": False,
                    "approved_date": False,
                    "reviewer_id": False,
                    "review_date": False,
                    "internal_sign_date": False,
                }
            )
            record._close_activities()

            record.message_post(
                body=_(
                    "✅ Ban Giám đốc %s đã duyệt yêu cầu đưa hợp đồng về nháp. Hợp đồng hiện đang ở trạng thái Nháp."
                )
                % self.env.user.name,
                subject=_("BGĐ Duyệt về nháp"),
            )

    def action_reject_draft(self):
        """Trưởng phòng hoặc Ban Giám đốc từ chối yêu cầu đưa về nháp"""
        for record in self:
            if record.draft_request_state not in ["dept_pending", "bgd_pending"]:
                raise UserError(
                    _("Chỉ có thể từ chối khi đang chờ yêu cầu được phê duyệt!")
                )

            old_state = record.draft_request_state
            record.write({"draft_request_state": "rejected"})
            record._close_activities()

            level = "Trưởng phòng" if old_state == "dept_pending" else "Ban Giám đốc"
            record.message_post(
                body=_("❌ %s %s đã từ chối yêu cầu đưa hợp đồng về nháp.")
                % (level, self.env.user.name),
                subject=_("Từ chối về nháp"),
            )

    # ============ NOTIFICATION METHODS ============
    def _send_approval_notification(self):
        """Gửi email thông báo cho người phê duyệt"""
        self.ensure_one()
        template = self.env.ref(
            "trasas_contract_management.email_template_contract_approval_request",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_approved_notification(self):
        """Gửi email thông báo đã được phê duyệt"""
        self.ensure_one()
        template = self.env.ref(
            "trasas_contract_management.email_template_contract_approved",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_rejected_notification(self):
        """Gửi email thông báo bị từ chối"""
        self.ensure_one()
        template = self.env.ref(
            "trasas_contract_management.email_template_contract_rejected",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_seal_notification(self):
        """Gửi email thông báo cho HCNS để đóng dấu"""
        self.ensure_one()
        template = self.env.ref(
            "trasas_contract_management.email_template_contract_seal_request",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    # ============ CRON JOB METHODS ============
    @api.model
    def _cron_check_expiring_contracts(self):
        """
        [B20] Cron job: Kiểm tra hợp đồng sắp hết hạn
        Chạy mỗi ngày lúc 1:00 AM

        - Gửi cảnh báo 30 ngày trước khi hết hạn
        - Tạo Activity cho nhóm Vận hành
        - Tự động chuyển sang Expired khi hết hạn
        """
        today = fields.Date.context_today(self)

        # Lấy số ngày nhắc từ cấu hình (mặc định 30)
        reminder_days = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("trasas_contract_management.contract_reminder_days", 30)
        )

        # [B20] Tìm hợp đồng sắp hết hạn
        warning_date = today + timedelta(days=reminder_days)
        expiring_contracts = self.search(
            [
                ("state", "=", "signed"),
                ("date_end", ">=", today),
                ("date_end", "<=", warning_date),
            ]
        )

        for contract in expiring_contracts:
            contract._send_expiring_notification()

            # Tạo Activity cho nhóm Vận hành (tránh trùng lặp)
            existing_activities = contract.activity_ids.filtered(
                lambda a: a.summary and "hết hạn" in (a.summary or "").lower()
            )
            if not existing_activities:
                users = contract._get_users_from_group(
                    "trasas_contract_management.group_contract_user"
                )
                for user in users:
                    contract._schedule_activity(
                        user.id,
                        _("⚠️ HĐ sắp hết hạn (%s ngày): %s")
                        % (contract.days_to_expire, contract.name),
                        deadline=0,
                        note="B20 - Cảnh báo hợp đồng sắp hết hạn",
                    )

        # [B20] Tự động chuyển hợp đồng hết hạn sang trạng thái Expired
        expired_contracts = self.search(
            [
                ("state", "=", "signed"),
                ("date_end", "<", today),
            ]
        )

        for contract in expired_contracts:
            contract.write({"state": "expired"})
            contract.message_post(
                body=_(
                    "⏰ [B20] Hợp đồng đã hết hạn - Chuyển sang trạng thái Expired."
                ),
                subject=_("Hợp đồng hết hạn"),
            )

    @api.model
    def _cron_check_signing_deadline(self):
        """
        [B7-B8] Cron job: Kiểm tra hạn ký & cảnh báo
        Chạy mỗi ngày lúc 2:00 AM

        Gửi thông báo nhắc nhở khi gần đến hạn ký (7 ngày)
        """
        today = fields.Date.context_today(self)

        # [B7-B8] Tìm hợp đồng có hạn ký trong 7 ngày tới
        warning_date = today + timedelta(days=7)
        contracts = self.search(
            [
                ("state", "in", ["approved", "signing"]),
                ("sign_deadline", ">=", today),
                ("sign_deadline", "<=", warning_date),
            ]
        )

        for contract in contracts:
            contract._send_signing_deadline_notification()

    def _send_expiring_notification(self):
        """Gửi email thông báo hợp đồng sắp hết hạn"""
        self.ensure_one()
        template = self.env.ref(
            "trasas_contract_management.email_template_contract_expiring",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_signing_deadline_notification(self):
        """Gửi email nhắc nhở hạn ký"""
        self.ensure_one()
        template = self.env.ref(
            "trasas_contract_management.email_template_signing_deadline",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    # ============ SIGN ACTIONS ============
    def action_view_sign_requests(self):
        """Mở danh sách yêu cầu ký liên quan"""
        self.ensure_one()
        return {
            "name": _("Yêu cầu ký"),
            "type": "ir.actions.act_window",
            "res_model": "sign.request",
            "view_mode": "list,form",
            "domain": [("contract_id", "=", self.id)],
            "context": {"default_contract_id": self.id},
        }

    def action_create_sign_request(self):
        """Tạo yêu cầu ký mới"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Tạo yêu cầu ký"),
            "res_model": "sign.request",
            "view_mode": "form",
            "context": {
                "default_contract_id": self.id,
                "default_subject": self.name + " - " + self.title,
            },
        }


# Extend Sign Request to link back to Contract
class SignRequest(models.Model):
    _inherit = "sign.request"

    contract_id = fields.Many2one("trasas.contract", string="Hợp đồng TRASAS")
