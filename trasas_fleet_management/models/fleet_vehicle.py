# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    vehicle_code = fields.Char(
        string="Mã phương tiện",
        readonly=True,
        copy=False,
        tracking=True,
        help="Định dạng: STT.YY/PT-TRS",
    )

    state = fields.Selection(
        [
            ("draft", "Phương tiện mới"),
            ("ready", "Sẵn sàng sử dụng"),
            ("in_use", "Đang sử dụng"),
            ("registration", "Đăng kiểm"),
            ("expired", "Hết hạn giấy tờ"),
            ("suspended", "Tạm ngưng sử dụng"),
            ("liquidated", "Đã thanh lý"),
        ],
        string="Trạng thái TRASAS",
        default="draft",
        tracking=True,
    )

    start_use_date = fields.Date(string="Ngày bắt đầu sử dụng", tracking=True)

    maintenance_type = fields.Selection(
        [("3", "3 tháng"), ("6", "6 tháng"), ("12", "12 tháng")],
        string="Loại bảo dưỡng định kỳ",
        tracking=True,
    )

    next_maintenance_date = fields.Date(
        string="Ngày bảo dưỡng tiếp theo",
        compute="_compute_next_maintenance_date",
        store=True,
        tracking=True,
    )

    legal_document_ids = fields.One2many(
        "fleet.legal.document", "vehicle_id", string="Hồ sơ pháp lý"
    )

    document_folder_id = fields.Many2one(
        "documents.document",
        string="Folder tài liệu",
        domain="[('type', '=', 'folder')]",
        readonly=True,
        copy=False,
    )

    def _get_or_create_document_folder(self):
        """Lấy hoặc tạo sub-folder trong Documents cho xe này."""
        self.ensure_one()
        if self.document_folder_id:
            return self.document_folder_id

        # Tìm folder "Vehicles" (folder type trong documents.document)
        Document = self.env["documents.document"]
        vehicles_folder = Document.search(
            [
                ("name", "=", "Vehicles"),
                ("type", "=", "folder"),
            ],
            limit=1,
        )
        if not vehicles_folder:
            # Nếu chưa có folder Vehicles, tạo mới ở root
            vehicles_folder = Document.create(
                {
                    "name": "Vehicles",
                    "type": "folder",
                }
            )

        # Tạo sub-folder cho xe
        vehicle_folder = Document.create(
            {
                "name": self.display_name,
                "type": "folder",
                "folder_id": vehicles_folder.id,
            }
        )
        self.document_folder_id = vehicle_folder
        return vehicle_folder

    # -------------------------------------------------------------------------
    # STATE SYNC: state (Selection) ↔ state_id (Many2one)
    # -------------------------------------------------------------------------

    # Mapping: state value → XML ID of fleet.vehicle.state record
    STATE_TO_XMLID = {
        "draft": "fleet.fleet_vehicle_state_new_request",
        "ready": "trasas_fleet_management.fleet_vehicle_state_trasas_ready",
        "in_use": "fleet.fleet_vehicle_state_registered",
        "registration": "trasas_fleet_management.fleet_vehicle_state_trasas_registration",
        "maintenance": "trasas_fleet_management.fleet_vehicle_state_trasas_maintenance",
        "repair": "trasas_fleet_management.fleet_vehicle_state_trasas_repair",
        "expired": "trasas_fleet_management.fleet_vehicle_state_trasas_expired",
        "suspended": "trasas_fleet_management.fleet_vehicle_state_trasas_suspended",
        "liquidated": "trasas_fleet_management.fleet_vehicle_state_trasas_liquidated",
    }

    def _sync_state_id(self, state_val):
        """Đồng bộ state_id (Many2one) theo state (Selection)."""
        xmlid = self.STATE_TO_XMLID.get(state_val)
        if xmlid:
            state_rec = self.env.ref(xmlid, raise_if_not_found=False)
            if state_rec:
                return state_rec.id
        return False

    def _sync_state_from_id(self, state_id_val):
        """Đồng bộ state (Selection) theo state_id (Many2one)."""
        if not state_id_val:
            return False

        # Tạo mapping ngược từ XMLID_TO_STATE
        xmlid_to_state = {v: k for k, v in self.STATE_TO_XMLID.items()}

        # Lấy XML ID của record state_id hiện tại
        state_rec = self.env["fleet.vehicle.state"].browse(state_id_val)
        res = state_rec.get_metadata()
        if res:
            xmlid = res[0].get("xmlid")
            return xmlid_to_state.get(xmlid, False)
        return False

    @api.onchange("state_id")
    def _onchange_state_id_trasas(self):
        """Khi người dùng click vào Statusbar (state_id), cập nhật state ngay lập tức để hiện/ẩn nút."""
        for rec in self:
            if rec.state_id:
                new_state = rec._sync_state_from_id(rec.state_id.id)
                if new_state:
                    rec.state = new_state

    @api.model
    def _trasas_sync_standard_states(self):
        """Đổi tên state gốc của Fleet và ẩn state không dùng.
        Gọi qua <function> trong XML data mỗi lần upgrade."""
        mapping = {
            "fleet.fleet_vehicle_state_new_request": {
                "name": "Phương tiện mới",
                "sequence": 1,
                "fold": False,
            },
            "fleet.fleet_vehicle_state_registered": {
                "name": "Đang sử dụng",
                "sequence": 30,
                "fold": False,
            },
            "fleet.fleet_vehicle_state_to_order": {"fold": True, "sequence": 998},
            "fleet.fleet_vehicle_state_downgraded": {"fold": True, "sequence": 999},
        }
        for xmlid, vals in mapping.items():
            state = self.env.ref(xmlid, raise_if_not_found=False)
            if state:
                state.write(vals)

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("vehicle_code"):
                vals["vehicle_code"] = (
                    self.env["ir.sequence"].next_by_code("fleet.vehicle.trasas") or "/"
                )
            # Đồng bộ state_id khi tạo mới
            state_val = vals.get("state", "draft")
            synced_id = self._sync_state_id(state_val)
            if synced_id:
                vals["state_id"] = synced_id
        return super().create(vals_list)

    @api.depends("start_use_date", "maintenance_type")
    def _compute_next_maintenance_date(self):
        for rec in self:
            if rec.start_use_date and rec.maintenance_type:
                months = int(rec.maintenance_type)
                rec.next_maintenance_date = rec.start_use_date + relativedelta(
                    months=months
                )
            else:
                rec.next_maintenance_date = False

    def write(self, vals):
        # 1. Nếu đổi state (Selection), cập nhật state_id
        if "state" in vals and "state_id" not in vals:
            synced_id = self._sync_state_id(vals["state"])
            if synced_id:
                vals["state_id"] = synced_id

        # 2. Nếu đổi state_id (Many2one), cập nhật state
        elif "state_id" in vals and "state" not in vals:
            new_state = self._sync_state_from_id(vals["state_id"])
            if new_state:
                vals["state"] = new_state

        # 3. Kiểm tra ràng buộc khi chuyển sang Sẵn sàng (ready)
        # Chỉ kiểm tra nếu đổi từ UI (không có skip_validation trong context)
        if not self.env.context.get("skip_validation"):
            new_state = vals.get("state")
            for rec in self:
                if new_state == "ready" and rec.state != "ready":
                    rec._check_mandatory_documents()

                # Chuyển sang Đang sử dụng (in_use)
                if new_state == "in_use" and rec.state != "in_use":
                    if not vals.get(
                        "start_use_date", rec.start_use_date
                    ) or not vals.get("maintenance_type", rec.maintenance_type):
                        raise UserError(
                            _(
                                "Vui lòng nhập Ngày bắt đầu sử dụng và Loại bảo dưỡng định kỳ trước khi đưa vào sử dụng."
                            )
                        )

        return super().write(vals)

    def _check_mandatory_documents(self):
        """Kiểm tra các hồ sơ bắt buộc trước khi cho phép Ready."""
        self.ensure_one()
        today = fields.Date.today()
        required_docs = {
            "registration": "Giấy đăng ký xe",
            "inspection": "Phiếu đăng kiểm",
            "insurance": "Bảo hiểm xe",
        }

        missing_docs = []
        for doc_type, label in required_docs.items():
            # Tìm giấy tờ tương ứng
            docs = self.legal_document_ids.filtered(
                lambda d: d.document_type == doc_type
            )

            if not docs:
                missing_docs.append(f"- Thiếu {label}")
            else:
                # Kiểm tra xem có file đính kèm không
                if not any(d.attachment_ids for d in docs):
                    missing_docs.append(f"- {label} chưa có file đính kèm")

                # Kiểm tra xem có bản nào còn hạn không
                active_docs = docs.filtered(
                    lambda d: not d.validity_date or d.validity_date >= today
                )
                if not active_docs:
                    missing_docs.append(f"- {label} đã hết hạn hiệu lực")

        if missing_docs:
            raise UserError(
                _("Hồ sơ phương tiện không đủ điều kiện để Sẵn sàng sử dụng:\n%s")
                % "\n".join(missing_docs)
            )

    # -------------------------------------------------------------------------
    # ACTIONS (State Transitions)
    # -------------------------------------------------------------------------

    def action_to_registration(self):
        """Mới -> Đăng kiểm"""
        for rec in self:
            if rec.state != "draft":
                continue
            rec.write({"state": "registration"})

    def action_set_ready(self):
        """Đăng kiểm -> Sẵn sàng. Kiểm tra các hồ sơ bắt buộc."""
        for rec in self:
            if rec.state != "registration":
                continue
            # Logic check đã nằm trong write()
            rec.write({"state": "ready"})

    def action_start_using(self):
        """Sẵn sàng -> Đang sử dụng"""
        for rec in self:
            if rec.state != "ready":
                continue
            # Logic check đã nằm trong write()
            rec.write({"state": "in_use"})

    def action_suspend(self):
        """Tạm ngưng để thanh lý"""
        for rec in self:
            rec.write({"state": "suspended"})

    def action_liquidate(self):
        """Thanh lý"""
        for rec in self:
            if rec.state != "suspended":
                raise UserError(
                    _("Cần chuyển qua trạng thái Tạm ngưng trước khi thanh lý.")
                )
            rec.write({"state": "liquidated", "active": False})

    # -------------------------------------------------------------------------
    # CRON / LOGIC
    # -------------------------------------------------------------------------

    @api.model
    def _cron_check_deadlines(self):
        """
        Daily Cron:
        Cảnh báo bảo trì dựa vào next_maintenance_date - 5 ngày.
        (Logic giấy tờ đã có trong Hồ sơ pháp lý).
        """
        today = fields.Date.today()
        vehicles = self.search([("state", "not in", ("liquidated", "expired"))])

        for v in vehicles:
            # 1. Bảo trì định kỳ (Dựa vào next_maintenance_date - 5 ngày)
            if v.next_maintenance_date:
                if today == v.next_maintenance_date - timedelta(days=5):
                    v._notify_maintenance_due()

            # 2. Cảnh báo định kỳ
            v._check_and_notify_alerts(today)

    def _check_and_notify_alerts(self, today):
        self.ensure_one()
        # Hiện tại tập trung vào bảo dưỡng, giấy tờ đã có module riêng
        pass

    def _notify_maintenance_due(self):
        self.ensure_one()
        # Thông báo cho tài xế và người chịu trách nhiệm
        users_to_notify = self.driver_id.user_id | self.manager_id
        for user in users_to_notify:
            if user:
                self.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=_("Lịch bảo dưỡng định kỳ xe %s") % self.vehicle_code,
                    note=_("Xe sắp đến hạn bảo dưỡng định kỳ (trong 5 ngày tới)."),
                    user_id=user.id,
                )
