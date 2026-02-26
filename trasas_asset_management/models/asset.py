# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class TrasasAsset(models.Model):
    """Model chính — Quản lý tài sản TRASAS

    Mã tài sản: STT.YY/TS-NHÓM-TRS (ví dụ: 01.26/TS-NXCT-TRS)

    5 nhóm trường:
    1. Thông tin định danh
    2. Thông tin mua sắm – ghi nhận
    3. Kế toán – Khấu hao
    4. Quản lý sử dụng
    5. Hồ sơ chứng từ đính kèm (notebook)

    + Trường riêng theo nhóm tài sản (conditional)
    """

    _name = "trasas.asset"
    _description = "Tài sản TRASAS"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    # =====================================================================
    # 1. THÔNG TIN ĐỊNH DANH
    # =====================================================================

    code = fields.Char(
        string="Mã tài sản",
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
        help="Tự động: STT.YY/TS-NHÓM-TRS",
    )
    name = fields.Char(
        string="Tên tài sản",
        required=True,
        tracking=True,
    )
    asset_group_id = fields.Many2one(
        "trasas.asset.type",
        string="Nhóm tài sản",
        required=True,
        tracking=True,
        help="Nhà cửa/CT / Máy móc / TB Văn phòng / Vô hình",
    )
    asset_group = fields.Selection(
        related="asset_group_id.group_code",
        string="Mã nhóm",
        store=True,
        help="Dùng để ẩn/hiện trường riêng theo nhóm",
    )

    asset_classification = fields.Selection(
        [
            ("internal", "Sử dụng nội bộ"),
            ("lease_out", "Cho thuê"),
            ("lease_in", "Thuê ngoài"),
        ],
        string="Phân loại",
        tracking=True,
        help="Phân loại tài sản: chỉ áp dụng cho nhóm Nhà cửa/CT và Máy móc TB SX",
    )

    description = fields.Html(
        string="Mô tả chi tiết",
    )

    # =====================================================================
    # 2. THÔNG TIN MUA SẮM – GHI NHẬN
    # =====================================================================

    supplier_id = fields.Many2one(
        "res.partner",
        string="Nhà cung cấp",
        tracking=True,
    )
    acquisition_date = fields.Date(
        string="Ngày mua / ghi nhận",
        tracking=True,
    )
    purchase_reference = fields.Char(
        string="Số HĐ / PO / Hóa đơn",
        tracking=True,
    )
    original_value = fields.Monetary(
        string="Nguyên giá",
        tracking=True,
        currency_field="currency_id",
        help="Giá mua + chi phí liên quan",
    )
    residual_value = fields.Monetary(
        string="Giá trị còn lại",
        tracking=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Tiền tệ",
        related="company_id.currency_id",
        store=True,
    )

    # =====================================================================
    # 3. KẾ TOÁN – KHẤU HAO
    # =====================================================================

    depreciation_start_date = fields.Date(
        string="Ngày bắt đầu khấu hao",
        tracking=True,
    )
    depreciation_duration = fields.Integer(
        string="Thời gian khấu hao (tháng)",
        tracking=True,
    )
    depreciation_method = fields.Selection(
        [
            ("linear", "Đường thẳng"),
            ("degressive", "Số dư giảm dần"),
        ],
        string="Phương pháp khấu hao",
        default="linear",
        tracking=True,
    )
    depreciation_rate = fields.Float(
        string="Tỷ lệ khấu hao (%/năm)",
        tracking=True,
    )
    # Kế toán accounts (requires module account)
    account_asset_id = fields.Many2one(
        "account.account",
        string="Fixed Asset Account",
        tracking=True,
        help="Tài khoản tài sản cố định",
    )
    account_depreciation_id = fields.Many2one(
        "account.account",
        string="Depreciation Account",
        tracking=True,
        help="Tài khoản khấu hao",
    )
    account_expense_id = fields.Many2one(
        "account.account",
        string="Expense Account",
        tracking=True,
        help="Tài khoản chi phí",
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        tracking=True,
    )

    # =====================================================================
    # 4. QUẢN LÝ SỬ DỤNG
    # =====================================================================

    department_id = fields.Many2one(
        "hr.department",
        string="Bộ phận sử dụng",
        tracking=True,
    )
    location = fields.Char(
        string="Vị trí tài sản",
        tracking=True,
        help="Chi nhánh, kho, phòng ban...",
    )
    responsible_user_id = fields.Many2one(
        "res.users",
        string="Người phụ trách",
        default=lambda self: self.env.user,
        tracking=True,
    )
    ownership_type = fields.Selection(
        [
            ("personal", "Cá nhân"),
            ("company", "Công ty"),
            ("government", "Nhà nước"),
            ("shared", "Đồng sở hữu"),
            ("leased", "Cho thuê"),
            ("leased_out", "Cho thuê ra bên ngoài"),
            ("ip", "Sở hữu trí tuệ / Bản quyền"),
        ],
        string="Hình thức sở hữu",
        tracking=True,
        help="Hình thức sở hữu tài sản",
    )
    state = fields.Selection(
        [
            ("draft", "Mới"),
            ("in_use", "Đang sử dụng"),
            # --- Thiết bị (MMTB, TBVP, TSVH) ---
            ("repair", "Sửa chữa"),
            ("maintenance", "Bảo trì định kỳ"),
            ("liquidated", "Thanh lý"),
            # --- Đất / Mặt bằng (NXCT) ---
            ("leased", "Cho thuê"),
            ("lease_in", "Thuê ngoài"),
            ("renovation", "Cải tạo"),
            ("expiring", "Sắp hết hạn (thuê)"),
            ("contract_ended", "Kết thúc HĐ thuê"),
            # --- Chung ---
            ("completed", "Hoàn thành"),
        ],
        string="Tình trạng",
        default="draft",
        required=True,
        tracking=True,
    )

    # ============ KANBAN STAGE ============
    stage_id = fields.Many2one(
        "trasas.asset.stage",
        string="Giai đoạn",
        tracking=True,
        index=True,
        copy=False,
        group_expand="_read_group_stage_ids",
        default=lambda self: self.env.ref(
            "trasas_asset_management.stage_draft",
            raise_if_not_found=False,
        ),
    )

    kanban_state = fields.Selection(
        [
            ("normal", "Bình thường"),
            ("done", "Hoàn tất"),
            ("blocked", "Bị chặn"),
        ],
        string="Trạng thái Kanban",
        default="normal",
    )

    color = fields.Integer(string="Màu", default=0)

    priority = fields.Selection(
        [
            ("0", "Bình thường"),
            ("1", "Quan trọng"),
            ("2", "Rất quan trọng"),
        ],
        string="Mức ưu tiên",
        default="0",
    )

    legend_normal = fields.Char(
        related="stage_id.legend_normal",
        string="Kanban: Bình thường",
        readonly=True,
    )
    legend_blocked = fields.Char(
        related="stage_id.legend_blocked",
        string="Kanban: Bị chặn",
        readonly=True,
    )
    legend_done = fields.Char(
        related="stage_id.legend_done",
        string="Kanban: Hoàn tất",
        readonly=True,
    )

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Hiển thị tất cả stage trong Kanban kể cả khi trống"""
        return self.env["trasas.asset.stage"].search([], order="sequence")

    def _sync_stage_from_state(self):
        """Đồng bộ stage_id khi state thay đổi"""
        Stage = self.env["trasas.asset.stage"]
        for rec in self:
            stage = Stage.search([("state", "=", rec.state)], limit=1)
            if stage and rec.stage_id != stage:
                rec.stage_id = stage

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals:
            self._sync_stage_from_state()
        return res

    def init(self):
        """Gán stage cho tài sản cũ chưa có stage_id (chạy khi upgrade)"""
        state_to_xmlid = {
            "draft": "stage_draft",
            "in_use": "stage_in_use",
            "repair": "stage_repair",
            "maintenance": "stage_maintenance",
            "liquidated": "stage_liquidated",
            "leased": "stage_leased",
            "lease_in": "stage_lease_in",
            "renovation": "stage_renovation",
            "expiring": "stage_expiring",
            "contract_ended": "stage_contract_ended",
            "completed": "stage_completed",
        }
        for state, xmlid in state_to_xmlid.items():
            stage = self.env.ref(
                f"trasas_asset_management.{xmlid}",
                raise_if_not_found=False,
            )
            if stage:
                self.env.cr.execute(
                    """
                    UPDATE trasas_asset
                    SET stage_id = %s
                    WHERE state = %s AND (stage_id IS NULL)
                    """,
                    (stage.id, state),
                )

    # =====================================================================
    # 5. HỒ SƠ CHỨNG TỪ ĐÍNH KÈM (notebook lines)
    # =====================================================================

    legal_document_ids = fields.One2many(
        "trasas.asset.legal.document",
        "asset_id",
        string="Hồ sơ chứng từ",
    )
    legal_document_count = fields.Integer(
        string="Số hồ sơ",
        compute="_compute_legal_document_count",
    )

    # =====================================================================
    # TRƯỜNG RIÊNG: NHÓM NXCT (Nhà cửa / Công trình)
    # =====================================================================

    building_address = fields.Char(
        string="Địa chỉ công trình",
    )
    building_area = fields.Float(
        string="Diện tích (m²)",
    )
    building_scale = fields.Char(
        string="Quy mô",
    )
    construction_date = fields.Date(
        string="Ngày xây dựng",
    )
    completion_date = fields.Date(
        string="Ngày hoàn công",
    )
    ownership_info = fields.Text(
        string="Thông tin sở hữu / QSDĐ",
    )
    building_category = fields.Selection(
        [
            ("warehouse", "Kho"),
            ("office", "Văn phòng"),
            ("yard", "Bãi"),
            ("factory", "Nhà xưởng"),
            ("other", "Khác"),
        ],
        string="Hạng mục công trình",
    )

    # =====================================================================
    # TRƯỜNG RIÊNG: NHÓM MMTB (Máy móc thiết bị)
    # =====================================================================

    machine_model = fields.Char(
        string="Model",
    )
    serial_number = fields.Char(
        string="Serial Number",
    )
    technical_specs = fields.Text(
        string="Thông số kỹ thuật",
        help="Công suất, tải trọng...",
    )
    manufacture_year = fields.Char(
        string="Năm sản xuất",
    )
    manufacturer = fields.Char(
        string="Nhà sản xuất",
    )
    origin_country = fields.Char(
        string="Xuất xứ",
    )
    safety_inspection_date = fields.Date(
        string="Hạn kiểm định an toàn",
    )
    maintenance_note = fields.Text(
        string="Lịch bảo trì / bảo dưỡng",
    )

    # =====================================================================
    # TRƯỜNG RIÊNG: NHÓM TBVP (Thiết bị văn phòng)
    # =====================================================================

    equipment_serial = fields.Char(
        string="Serial / Asset Tag",
    )
    it_config = fields.Text(
        string="Cấu hình kỹ thuật",
        help="Đối với thiết bị IT",
    )
    warranty_expiry_date = fields.Date(
        string="Hạn bảo hành",
    )
    installation_location = fields.Char(
        string="Vị trí lắp đặt",
        help="Phòng ban, tầng, khu vực",
    )

    # =====================================================================
    # TRƯỜNG RIÊNG: NHÓM TSVH (Tài sản vô hình)
    # =====================================================================

    license_key = fields.Char(
        string="Mã bản quyền / License key",
    )
    license_provider = fields.Char(
        string="Nhà cung cấp bản quyền",
    )
    license_start_date = fields.Date(
        string="Ngày hiệu lực",
    )
    license_expiry_date = fields.Date(
        string="Ngày hết hạn",
    )
    license_quantity = fields.Integer(
        string="Số lượng user / license",
    )
    renewal_terms = fields.Text(
        string="Điều kiện gia hạn",
    )
    service_contract_ref = fields.Char(
        string="HĐ dịch vụ đi kèm",
    )

    # =====================================================================
    # GHI CHÚ + CÔNG TY
    # =====================================================================

    note = fields.Text(
        string="Ghi chú",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Công ty",
        default=lambda self: self.env.company,
        required=True,
    )

    # =====================================================================
    # COMPUTED
    # =====================================================================

    @api.depends("legal_document_ids")
    def _compute_legal_document_count(self):
        for rec in self:
            rec.legal_document_count = len(rec.legal_document_ids)

    # =====================================================================
    # ONCHANGE
    # =====================================================================

    @api.onchange("asset_group_id")
    def _onchange_asset_group_id(self):
        """Tự điền tỷ lệ khấu hao mặc định khi chọn nhóm"""
        if self.asset_group_id and self.asset_group_id.default_depreciation_rate:
            self.depreciation_rate = self.asset_group_id.default_depreciation_rate

    # =====================================================================
    # CRUD — Cấp mã tự động: STT.YY/TS-NHÓM-TRS
    # =====================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Cấp mã tài sản: STT.YY/TS-NHÓM-TRS
        Ví dụ: 01.26/TS-NXCT-TRS
        """
        for vals in vals_list:
            if not vals.get("code") or vals.get("code") == "New":
                asset_type = self.env["trasas.asset.type"].browse(
                    vals.get("asset_group_id")
                )
                if asset_type and asset_type.sequence_id:
                    vals["code"] = asset_type.sequence_id.next_by_id()
                else:
                    vals["code"] = (
                        self.env["ir.sequence"].next_by_code("trasas.asset") or "TS/NEW"
                    )
        records = super().create(vals_list)

        for rec in records:
            rec._schedule_activity_upload_documents()
            rec._send_asset_created_notification()
            rec.message_post(
                body=_("Tài sản đã được tạo với mã: %s") % rec.code,
                subject=_("Tạo tài sản mới"),
            )
        return records

    # =====================================================================
    # STATE TRANSITIONS — CHUNG
    # =====================================================================

    def action_confirm(self):
        """Mới → Đang sử dụng (áp dụng tất cả nhóm)"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(
                    _("Chỉ tài sản trạng thái Mới mới có thể đưa vào sử dụng!")
                )
            rec.write({"state": "in_use"})
            rec._close_activities()
            rec.message_post(
                body=_("✅ Tài sản đã đưa vào sử dụng."),
                subject=_("Kích hoạt tài sản"),
            )
            rec._send_state_change_notification()

    def action_completed(self):
        """→ Hoàn thành (áp dụng tất cả nhóm)"""
        allowed = ("liquidated", "contract_ended", "in_use")
        for rec in self:
            if rec.state not in allowed:
                raise UserError(
                    _(
                        "Chỉ tài sản trạng thái Thanh lý, Kết thúc HĐ hoặc Đang sử dụng mới có thể Hoàn thành!"
                    )
                )
            rec.write({"state": "completed"})
            rec.message_post(
                body=_("🏁 Tài sản đã hoàn thành."),
                subject=_("Hoàn thành tài sản"),
            )
            rec._send_state_change_notification()

    def action_set_to_draft(self):
        """Đặt về Mới"""
        for rec in self:
            rec.write({"state": "draft"})
            rec.message_post(
                body=_("Tài sản đã được đặt về trạng thái Mới."),
                subject=_("Đặt về Mới"),
            )

    # =====================================================================
    # STATE TRANSITIONS — THIẾT BỊ (MMTB, TBVP, TSVH)
    # =====================================================================

    def action_repair(self):
        """Đang sử dụng → Sửa chữa"""
        for rec in self:
            if rec.state != "in_use":
                raise UserError(
                    _("Chỉ tài sản Đang sử dụng mới có thể chuyển Sửa chữa!")
                )
            rec.write({"state": "repair"})
            rec.message_post(
                body=_("🔧 Tài sản đang sửa chữa."),
                subject=_("Sửa chữa tài sản"),
            )
            rec._send_state_change_notification()

    def action_maintenance(self):
        """Đang sử dụng → Bảo trì định kỳ"""
        for rec in self:
            if rec.state != "in_use":
                raise UserError(
                    _("Chỉ tài sản Đang sử dụng mới có thể chuyển Bảo trì!")
                )
            rec.write({"state": "maintenance"})
            rec.message_post(
                body=_("🔧 Tài sản đang bảo trì định kỳ."),
                subject=_("Bảo trì định kỳ"),
            )
            rec._send_state_change_notification()

    def action_return_to_use(self):
        """Sửa chữa / Bảo trì → Đang sử dụng"""
        for rec in self:
            if rec.state not in ("repair", "maintenance"):
                raise UserError(
                    _(
                        "Chỉ tài sản đang Sửa chữa hoặc Bảo trì mới có thể đưa lại vào sử dụng!"
                    )
                )
            rec.write({"state": "in_use"})
            rec.message_post(
                body=_("✅ Tài sản đã đưa lại vào sử dụng."),
                subject=_("Hoàn tất sửa chữa / bảo trì"),
            )
            rec._send_state_change_notification()

    def action_liquidate(self):
        """Đang sử dụng / Sửa chữa / Bảo trì → Thanh lý"""
        for rec in self:
            if rec.state not in ("in_use", "repair", "maintenance"):
                raise UserError(
                    _(
                        "Chỉ tài sản Đang sử dụng, Sửa chữa hoặc Bảo trì mới có thể Thanh lý!"
                    )
                )
            rec.write({"state": "liquidated"})
            rec.message_post(
                body=_("🗑️ Tài sản đã thanh lý."),
                subject=_("Thanh lý tài sản"),
            )
            rec._send_state_change_notification()

    # =====================================================================
    # STATE TRANSITIONS — ĐẤT / MẶT BẰNG (NXCT)
    # =====================================================================

    def action_lease(self):
        """Đang sử dụng → Cho thuê"""
        for rec in self:
            if rec.state != "in_use":
                raise UserError(_("Chỉ tài sản Đang sử dụng mới có thể Cho thuê!"))
            rec.write({"state": "leased"})
            rec.message_post(
                body=_("🏠 Tài sản đã cho thuê."),
                subject=_("Cho thuê tài sản"),
            )
            rec._send_state_change_notification()

    def action_lease_direct(self):
        """Mới → Cho thuê (từ phân loại Cho thuê)"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Chỉ tài sản trạng thái Mới!"))
            rec.write({"state": "leased"})
            rec._close_activities()
            rec.message_post(
                body=_("🏠 Tài sản đã cho thuê."),
                subject=_("Cho thuê tài sản"),
            )
            rec._send_state_change_notification()

    def action_lease_in(self):
        """Mới → Thuê ngoài (từ phân loại Thuê ngoài)"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Chỉ tài sản trạng thái Mới!"))
            rec.write({"state": "lease_in"})
            rec._close_activities()
            rec.message_post(
                body=_("📋 Tài sản thuê ngoài đã kích hoạt."),
                subject=_("Thuê ngoài tài sản"),
            )
            rec._send_state_change_notification()

    def action_renovation(self):
        """Đang sử dụng → Cải tạo"""
        for rec in self:
            if rec.state != "in_use":
                raise UserError(_("Chỉ tài sản Đang sử dụng mới có thể Cải tạo!"))
            rec.write({"state": "renovation"})
            rec.message_post(
                body=_("🏗️ Tài sản đang cải tạo."),
                subject=_("Cải tạo tài sản"),
            )
            rec._send_state_change_notification()

    def action_return_from_renovation(self):
        """Cải tạo → Đang sử dụng"""
        for rec in self:
            if rec.state != "renovation":
                raise UserError(
                    _("Chỉ tài sản đang Cải tạo mới có thể đưa lại vào sử dụng!")
                )
            rec.write({"state": "in_use"})
            rec.message_post(
                body=_("✅ Cải tạo hoàn tất — Đưa lại vào sử dụng."),
                subject=_("Hoàn tất cải tạo"),
            )
            rec._send_state_change_notification()

    def action_expiring(self):
        """Cho thuê → Sắp hết hạn (thuê)"""
        for rec in self:
            if rec.state != "leased":
                raise UserError(
                    _("Chỉ tài sản Cho thuê mới có thể đánh dấu Sắp hết hạn!")
                )
            rec.write({"state": "expiring"})
            rec.message_post(
                body=_("⚠️ Hợp đồng thuê sắp hết hạn."),
                subject=_("Sắp hết hạn thuê"),
            )
            rec._send_state_change_notification()

    def action_contract_ended(self):
        """Cho thuê / Sắp hết hạn → Kết thúc HĐ thuê"""
        for rec in self:
            if rec.state not in ("leased", "expiring"):
                raise UserError(
                    _("Chỉ tài sản Cho thuê hoặc Sắp hết hạn mới có thể Kết thúc HĐ!")
                )
            rec.write({"state": "contract_ended"})
            rec.message_post(
                body=_("📋 Hợp đồng thuê đã kết thúc."),
                subject=_("Kết thúc HĐ thuê"),
            )
            rec._send_state_change_notification()

    def action_return_to_use_from_lease(self):
        """Kết thúc HĐ thuê → Đang sử dụng (tái sử dụng)"""
        for rec in self:
            if rec.state != "contract_ended":
                raise UserError(
                    _("Chỉ tài sản Kết thúc HĐ mới có thể đưa lại vào sử dụng!")
                )
            rec.write({"state": "in_use"})
            rec.message_post(
                body=_("✅ Tài sản tái sử dụng sau khi kết thúc HĐ thuê."),
                subject=_("Tái sử dụng tài sản"),
            )
            rec._send_state_change_notification()

    # =====================================================================
    # ACTIVITY SCHEDULING
    # =====================================================================

    def _schedule_activity_upload_documents(self):
        """Sau khi tạo, nhắc upload hồ sơ chứng từ"""
        for rec in self:
            if not rec.responsible_user_id:
                continue
            rec.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=rec.responsible_user_id.id,
                summary=_("Upload hồ sơ tài sản %s") % rec.code,
                note=_(
                    'Tài sản "%s" (Mã: %s) đã được tạo.\n'
                    "Vui lòng upload hồ sơ chứng từ: HĐ, hóa đơn, "
                    "biên bản bàn giao, hồ sơ kỹ thuật..."
                )
                % (rec.name, rec.code),
                date_deadline=fields.Date.context_today(rec) + timedelta(days=7),
            )

    def _schedule_activity_confirm_asset(self):
        """Nhắc manager xác nhận đưa vào sử dụng"""
        manager_users = self._get_users_from_group(
            "trasas_asset_management.group_asset_manager"
        )
        for rec in self:
            for user in manager_users:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=user.id,
                    summary=_("Xác nhận tài sản %s") % rec.code,
                    note=_(
                        'Hồ sơ tài sản "%s" (Mã: %s) đã sẵn sàng.\n'
                        "Kiểm tra và đưa vào sử dụng."
                    )
                    % (rec.name, rec.code),
                    date_deadline=fields.Date.context_today(rec) + timedelta(days=3),
                )

    def _close_activities(self):
        """Đóng tất cả Activity cũ"""
        self.activity_feedback(["mail.mail_activity_data_todo"])

    # =====================================================================
    # HELPER
    # =====================================================================

    def _get_users_from_group(self, group_xmlid):
        group = self.env.ref(group_xmlid, raise_if_not_found=False)
        if group:
            return group.users.filtered(lambda u: u.active)
        return self.env["res.users"]

    # =====================================================================
    # EMAIL NOTIFICATIONS
    # =====================================================================

    def _send_asset_created_notification(self):
        self.ensure_one()
        template = self.env.ref(
            "trasas_asset_management.email_template_asset_created",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_state_change_notification(self):
        self.ensure_one()
        template = self.env.ref(
            "trasas_asset_management.email_template_asset_state_changed",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_expiring_document_notification(self, doc):
        self.ensure_one()
        template = self.env.ref(
            "trasas_asset_management.email_template_document_expiring",
            raise_if_not_found=False,
        )
        if template:
            template.with_context(legal_doc=doc).send_mail(self.id, force_send=True)

    def _send_expired_document_notification(self, doc):
        self.ensure_one()
        template = self.env.ref(
            "trasas_asset_management.email_template_document_expired",
            raise_if_not_found=False,
        )
        if template:
            template.with_context(legal_doc=doc).send_mail(self.id, force_send=True)

    # =====================================================================
    # CRON JOB
    # =====================================================================

    @api.model
    def _cron_check_expiring_documents(self):
        """Kiểm tra giấy tờ sắp hết hạn / đã hết hạn"""
        today = fields.Date.context_today(self)
        LegalDoc = self.env["trasas.asset.legal.document"]

        # Sắp hết hạn (30 ngày)
        warning_date = today + timedelta(days=30)
        expiring_docs = LegalDoc.search(
            [
                ("state", "=", "active"),
                ("validity_date", ">=", today),
                ("validity_date", "<=", warning_date),
            ]
        )
        for doc in expiring_docs:
            doc.write({"state": "expiring_soon"})
            asset = doc.asset_id
            if asset.responsible_user_id:
                asset.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=asset.responsible_user_id.id,
                    summary=_('Giấy tờ "%s" sắp hết hạn (%s)')
                    % (doc.name, doc.validity_date),
                    note=_("Số GCN: %s\nHết hạn: %s\nCòn %s ngày")
                    % (
                        doc.certificate_number or "N/A",
                        doc.validity_date,
                        doc.days_to_expire,
                    ),
                    date_deadline=doc.validity_date,
                )
            asset._send_expiring_document_notification(doc)
            asset.message_post(
                body=_('⚠️ Giấy tờ "%s" (GCN: %s) sắp hết hạn vào %s')
                % (doc.name, doc.certificate_number or "N/A", doc.validity_date),
            )

        # Đã hết hạn
        expired_docs = LegalDoc.search(
            [
                ("state", "in", ["active", "expiring_soon"]),
                ("validity_date", "<", today),
            ]
        )
        for doc in expired_docs:
            doc.write({"state": "expired"})
            asset = doc.asset_id
            asset._send_expired_document_notification(doc)
            asset.message_post(
                body=_('❌ Giấy tờ "%s" (GCN: %s) đã hết hiệu lực!')
                % (doc.name, doc.certificate_number or "N/A"),
            )

    # =====================================================================
    # SMART BUTTONS
    # =====================================================================

    def action_view_legal_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Hồ sơ — %s") % self.name,
            "res_model": "trasas.asset.legal.document",
            "view_mode": "list,form",
            "domain": [("asset_id", "=", self.id)],
            "context": {"default_asset_id": self.id},
        }
