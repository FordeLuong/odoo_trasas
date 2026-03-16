from odoo import models, fields, _


class TrasasDispatchIncoming(models.Model):
    _inherit = "trasas.dispatch.incoming"

    # --- Liên kết công văn đi ---
    outgoing_dispatch_ids = fields.One2many(
        "trasas.dispatch.outgoing",
        "incoming_dispatch_id",
        string="Công văn đi phản hồi",
    )
    outgoing_dispatch_count = fields.Integer(
        string="Số CV đi",
        compute="_compute_outgoing_dispatch_count",
    )

    def _compute_outgoing_dispatch_count(self):
        for record in self:
            record.outgoing_dispatch_count = len(record.outgoing_dispatch_ids)

    def action_view_outgoing_dispatches(self):
        """Mở danh sách công văn đi phản hồi"""
        self.ensure_one()
        return {
            "name": _("Công văn đi phản hồi"),
            "type": "ir.actions.act_window",
            "res_model": "trasas.dispatch.outgoing",
            "view_mode": "list,form",
            "domain": [("incoming_dispatch_id", "=", self.id)],
            "context": {"default_incoming_dispatch_id": self.id},
        }

    def action_confirm(self):
        """Override to auto-create outgoing dispatch if response is required (Direct flow)"""
        res = super().action_confirm()
        for record in self:
            # Chỉ tạo nếu không qua bước Quản lý phân công (đã có handler_ids ngay từ đầu)
            if not record.is_via_manager and record.response_required and record.handler_ids:
                record._auto_create_outgoing_dispatch()
        return res

    def action_manager_assign(self):
        """Override to auto-create outgoing dispatch when Manager assigns handlers"""
        res = super().action_manager_assign()
        for record in self:
            if record.response_required and record.handler_ids:
                record._auto_create_outgoing_dispatch()
        return res

    def _auto_create_outgoing_dispatch(self):
        """Helper to create a draft outgoing dispatch based on incoming data"""
        self.ensure_one()
        if not self.handler_ids:
            return

        # Check if already exists to avoid duplication
        existing = self.env["trasas.dispatch.outgoing"].search(
            [("incoming_dispatch_id", "=", self.id)], limit=1
        )
        if existing:
            return

        handler = self.handler_ids[0]
        subject = _("Phản hồi công văn số %s – %s") % (
            self.dispatch_number or self.name,
            self.extract_content or "",
        )
        
        self.env["trasas.dispatch.outgoing"].create({
            "subject": subject,
            "incoming_dispatch_id": self.id,
            "recipient_id": self.sender_id.id,
            "drafter_id": handler.id,
        })
        
        self.message_post(
            body=_("Hệ thống đã tự động tạo Công văn đi dự thảo cho người xử lý %s.") % handler.name,
            subtype_xmlid="mail.mt_note",
        )
