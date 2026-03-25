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
        """Override to remove auto-creation (Manual flow now)"""
        return super().action_confirm()

    def action_manager_assign(self):
        """Override to remove auto-creation (Manual flow now)"""
        return super().action_manager_assign()

    def action_create_outgoing_dispatch(self):
        """Manual action to create a draft outgoing dispatch based on incoming data"""
        self.ensure_one()
        from odoo import _
        from odoo.exceptions import UserError

        if not self.handler_ids:
            raise UserError(_("Vui lòng chọn Người xử lý trước khi tạo công văn đi phản hồi!"))

        # Check if already exists to avoid duplication (limit to 1 draft/active one)
        existing = self.env["trasas.dispatch.outgoing"].search(
            [("incoming_dispatch_id", "=", self.id), ("state", "!=", "cancel")], limit=1
        )
        if existing:
            return {
                "name": _("Công văn đi phản hồi"),
                "type": "ir.actions.act_window",
                "res_model": "trasas.dispatch.outgoing",
                "res_id": existing.id,
                "view_mode": "form",
                "target": "current",
            }

        if not self.sender_id:
            raise UserError(_("Vui lòng điền thông tin 'Nơi gửi' để xác định nơi nhận cho công văn phản hồi!"))

        handler = self.handler_ids[0]
        subject = _("Phản hồi công văn số %s – %s") % (
            self.dispatch_number or self.name,
            self.extract_content or "",
        )
        
        outgoing = self.env["trasas.dispatch.outgoing"].create({
            "subject": subject,
            "incoming_dispatch_id": self.id,
            "recipient_id": self.sender_id.id,
            "drafter_id": handler.id,
        })
        
        self.message_post(
            body=_("Công văn đi dự thảo đã được tạo bởi %s.") % self.env.user.name,
            subtype_xmlid="mail.mt_note",
        )

        return {
            "name": _("Công văn đi phản hồi"),
            "type": "ir.actions.act_window",
            "res_model": "trasas.dispatch.outgoing",
            "res_id": outgoing.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_no_response_needed(self):
        """Override to cancel linked outgoing dispatches if any"""
        res = super().action_no_response_needed()
        for record in self:
            if record.outgoing_dispatch_ids:
                active_outgoing = record.outgoing_dispatch_ids.filtered(lambda x: x.state != 'cancel')
                if active_outgoing:
                    active_outgoing.action_cancel()
                    record.message_post(body=_("Các công văn đi phản hồi liên quan đã được tự động hủy."))
        return res

