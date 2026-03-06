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
        """Override to auto-create outgoing dispatch if response is required"""
        res = super().action_confirm()

        for record in self:
            # TH1: Tự động tạo công văn đi phản hồi khi cần
            if record.response_required and record.handler_ids:
                handler = record.handler_ids[0]
                subject = "Phản hồi công văn số %s – %s" % (
                    record.name,
                    record.extract_content or "",
                )
                existing_outgoing = self.env["trasas.dispatch.outgoing"].search(
                    [("incoming_dispatch_id", "=", record.id)], limit=1
                )
                if not existing_outgoing:
                    self.env["trasas.dispatch.outgoing"].create(
                        {
                            "subject": subject,
                            "incoming_dispatch_id": record.id,
                            "recipient_id": record.sender_id.id,
                            "drafter_id": handler.id,
                        }
                    )
                    record.message_post(
                        body=_(
                            "Hệ thống đã tự động tạo Công văn đi phản hồi cho người xử lý %s."
                        )
                        % handler.name,
                        subtype_xmlid="mail.mt_note",
                    )
        return res
