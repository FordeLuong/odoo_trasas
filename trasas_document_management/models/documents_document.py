# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import timedelta


class TrasasDocumentType(models.Model):
    _name = "trasas.document.type"
    _description = "Loại hồ sơ (TRASAS)"
    _order = "sequence, id"

    name = fields.Char(string="Tên loại hồ sơ", required=True)
    code = fields.Char(string="Mã", copy=False)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(string="Thứ tự", default=10)
    folder_id = fields.Many2one(
        "documents.document",
        string="Thư mục liên kết",
        ondelete="set null",
        copy=False,
        domain=[("type", "=", "folder")],
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_document_folder()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ["name", "active", "sequence"]):
            self._sync_document_folder()
        return res

    def unlink(self):
        # Lưu trữ thư mục liên kết trước khi xóa loại hồ sơ để tránh mồ côi dữ liệu
        for rec in self:
            if rec.folder_id:
                rec.folder_id.write({"active": False})
        return super().unlink()

    @api.model
    def _sync_document_folder(self, *args, **kwargs):
        """Tạo hoặc cập nhật thư mục tương ứng trong app Documents"""
        # Lấy ID của root folder từ XML data
        root_folder = self.env.ref(
            "trasas_document_management.workspace_trasas_internal_docs",
            raise_if_not_found=False,
        )
        if not root_folder:
            return

        # Duyệt qua cả các bản ghi đã active=False để đồng bộ trạng thái lưu trữ
        if self:
            records = self.with_context(active_test=False)
        else:
            records = (
                self.env["trasas.document.type"]
                .with_context(active_test=False)
                .search([])
            )

        for rec in records:
            folder_vals = {
                "name": rec.name,
                "type": "folder",
                "folder_id": root_folder.id,
                "active": rec.active,
                "access_internal": "edit",  # Tất cả internal users có thể xem + upload
            }
            # Nếu documents.document có field sequence thì đồng bộ luôn
            if "sequence" in self.env["documents.document"]._fields:
                folder_vals["sequence"] = rec.sequence

            if not rec.folder_id:
                # Chỉ tạo mới nếu bản ghi đang active
                if rec.active:
                    folder = self.env["documents.document"].create(folder_vals)
                    rec.with_context(tracking_disable=True).write(
                        {"folder_id": folder.id}
                    )
            else:
                rec.folder_id.write(folder_vals)


class DocumentsDocumentInherit(models.Model):
    """Kế thừa documents.document — Bổ sung trường thông tin cơ bản (B2b),
    trạng thái hiệu lực, và cảnh báo hết hạn (B5, B12)
    """

    _inherit = "documents.document"

    # =====================================================================
    # THÔNG TIN CƠ BẢN BỔ SUNG (B2b)
    # =====================================================================

    document_type_id = fields.Many2one(
        "trasas.document.type",
        string="Loại hồ sơ",
        tracking=True,
        help="Phân loại loại hình tài liệu",
    )

    document_number = fields.Char(
        string="Số hiệu văn bản",
        tracking=True,
    )

    issuing_authority = fields.Char(
        string="Cơ quan cấp / Ban hành",
        tracking=True,
    )

    issue_date = fields.Date(
        string="Ngày cấp / Ban hành",
        tracking=True,
    )

    validity_date = fields.Date(
        string="Ngày hết hiệu lực",
        tracking=True,
        help="Để trống nếu không có thời hạn",
    )

    days_to_expire = fields.Integer(
        string="Số ngày còn lại",
        compute="_compute_days_to_expire",
        store=True,
    )

    confidential_level = fields.Selection(
        [
            ("public", "Công khai"),
            ("restricted", "Giới hạn"),
            ("only me", "Chỉ mình tôi"),
        ],
        string="Độ mật",
        default="public",
        tracking=True,
    )

    doc_state = fields.Selection(
        [
            ("active", "Hiệu lực"),
            ("expiring_soon", "Sắp hết hạn"),
            ("expired", "Hết hiệu lực"),
        ],
        string="Trạng thái hiệu lực",
        default="active",
        tracking=True,
    )

    department_id = fields.Many2one(
        "hr.department",
        string="Phòng ban quản lý",
        tracking=True,
    )

    responsible_user_id = fields.Many2one(
        "res.users",
        string="Người phụ trách",
        default=lambda self: self.env.user,
        tracking=True,
    )
    # =====================================================================
    # SYNC confidential_level → access_internal (Odoo native permission)
    # =====================================================================

    _CONFIDENTIAL_TO_ACCESS = {
        "public": "edit",  # Tất cả internal user đều thấy + sửa
        "restricted": "view",  # Tất cả thấy file, nhưng nội dung bị khóa trừ khi được share
        "only me": "none",  # Chỉ owner thấy
    }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Chỉ áp dụng cho file (không phải folder)
            if vals.get("type") == "folder":
                continue
            if "confidential_level" in vals and "access_internal" not in vals:
                cl = vals["confidential_level"]
                vals["access_internal"] = self._CONFIDENTIAL_TO_ACCESS.get(cl, "none")
            elif "access_internal" not in vals:
                # Default confidential_level = "public" → access_internal = "edit"
                vals["access_internal"] = "edit"
        return super().create(vals_list)

    def write(self, vals):
        if "confidential_level" in vals:
            cl = vals["confidential_level"]
            vals["access_internal"] = self._CONFIDENTIAL_TO_ACCESS.get(cl, "none")
        return super().write(vals)

    # =====================================================================
    # COMPUTED
    # =====================================================================

    @api.depends("validity_date")
    def _compute_days_to_expire(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.validity_date:
                delta = rec.validity_date - today
                rec.days_to_expire = delta.days
            else:
                rec.days_to_expire = 0

    # =====================================================================
    # CAN ACCESS CONTENT — Kiểm tra user có quyền xem nội dung file
    # =====================================================================

    can_access_content = fields.Boolean(
        string="Có quyền truy cập nội dung",
        compute="_compute_can_access_content",
    )

    is_owner = fields.Boolean(
        string="Là chủ sở hữu",
        compute="_compute_is_owner",
    )

    @api.depends_context("uid")
    @api.depends("owner_id", "create_uid")
    def _compute_is_owner(self):
        user = self.env.user
        is_admin = user.has_group("base.group_system")
        is_manager = user.has_group("documents.group_documents_manager")
        for rec in self:
            if is_admin or is_manager:
                rec.is_owner = True
            elif rec.owner_id == user or rec.create_uid == user:
                rec.is_owner = True
            else:
                rec.is_owner = False

    @api.depends_context("uid")
    @api.depends("confidential_level", "owner_id", "access_ids")
    def _compute_can_access_content(self):
        user = self.env.user
        partner = user.partner_id
        is_manager = user.has_group("documents.group_documents_manager")
        is_admin = user.has_group("base.group_system")
        for rec in self:
            if rec.type == "folder":
                rec.can_access_content = True
                continue
            if is_admin or is_manager:
                rec.can_access_content = True
                continue
            if rec.confidential_level != "restricted":
                rec.can_access_content = True
                continue
            # restricted: chỉ owner hoặc người được share mới có quyền
            if rec.owner_id == user or rec.create_uid == user:
                rec.can_access_content = True
                continue
            # Kiểm tra documents.access — có bản ghi share cho partner hiện tại không
            has_access = rec.access_ids.filtered(lambda a: a.partner_id == partner)
            rec.can_access_content = bool(has_access)

    # =====================================================================
    # ACCESS REQUEST — Xin quyền truy cập file giới hạn
    # =====================================================================

    def action_request_access(self):
        """User xin quyền truy cập file giới hạn.
        Gửi thông báo chatter cho owner + tạo Activity nhắc việc.
        """
        self.ensure_one()
        user = self.env.user
        owner = self.owner_id or self.create_uid

        if not owner:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Lỗi"),
                    "message": _("Không tìm thấy chủ sở hữu file."),
                    "type": "danger",
                    "sticky": False,
                },
            }

        # Gửi message chatter cho owner
        self.sudo().message_post(
            body=_(
                "🔑 <b>%s</b> muốn truy cập tài liệu này. "
                "Vui lòng nhấn <b>Share</b> để cấp quyền."
            )
            % user.name,
            subject=_("Yêu cầu truy cập: %s") % self.name,
            partner_ids=[owner.partner_id.id],
            message_type="notification",
        )

        # Tạo Activity nhắc việc cho owner
        self.sudo().activity_schedule(
            "mail.mail_activity_data_todo",
            user_id=owner.id,
            summary=_("Xin truy cập: %s") % self.name,
            note=_(
                "<b>%s</b> yêu cầu truy cập tài liệu <b>%s</b>. "
                "Vui lòng vào file và nhấn Share để cấp quyền cho họ."
            )
            % (user.name, self.name),
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Đã gửi yêu cầu"),
                "message": _(
                    "Yêu cầu truy cập đã được gửi tới %s. Vui lòng chờ phê duyệt."
                )
                % owner.name,
                "type": "success",
                "sticky": False,
            },
        }

    # =====================================================================
    # CRON — Cảnh báo hết hạn (B5) & Đóng VB hết hiệu lực (B12)
    # =====================================================================

    @api.model
    def _cron_document_expiry_check(self):
        """Quét tài liệu hàng ngày:
        - Trước 30 ngày: Cảnh báo qua Activity
        - Đến hạn: Đổi state → expired + thông báo phòng ban
        - Trước 30 ngày: Đổi state → expiring_soon
        """
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=30)

        # 1. Tìm các VB sắp hết hạn (trong 30 ngày tới) + chưa được cảnh báo
        expiring_docs = self.search(
            [
                ("type", "!=", "folder"),
                ("doc_state", "=", "active"),
                ("validity_date", "!=", False),
                ("validity_date", "<=", warning_date),
                ("validity_date", ">", today),
            ]
        )

        for doc in expiring_docs:
            doc.write({"doc_state": "expiring_soon"})
            if doc.responsible_user_id:
                doc.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=doc.responsible_user_id.id,
                    note=_(
                        "Tài liệu '%s' (Số: %s) sẽ hết hiệu lực vào ngày %s. "
                        "Vui lòng xem xét gia hạn hoặc cập nhật."
                    )
                    % (
                        doc.name,
                        doc.document_number or "N/A",
                        doc.validity_date.strftime("%d/%m/%Y"),
                    ),
                    summary=_("Tài liệu sắp hết hiệu lực: %s") % doc.name,
                )

        # 2. Tìm các VB đã hết hạn → đóng
        expired_docs = self.search(
            [
                ("type", "!=", "folder"),
                ("doc_state", "in", ("active", "expiring_soon")),
                ("validity_date", "!=", False),
                ("validity_date", "<=", today),
            ]
        )

        for doc in expired_docs:
            doc.write({"doc_state": "expired"})
            doc._message_log(
                body=_(
                    "📛 Tài liệu đã hết hiệu lực từ ngày %s. Đã tự động chuyển trạng thái."
                )
                % doc.validity_date.strftime("%d/%m/%Y"),
            )

