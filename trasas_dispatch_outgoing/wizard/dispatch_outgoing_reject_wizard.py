# -*- coding: utf-8 -*-
from odoo import models, fields


class DispatchOutgoingRejectWizard(models.TransientModel):
    _name = "trasas.dispatch.outgoing.reject.wizard"
    _description = "Lý do từ chối công văn đi"

    dispatch_id = fields.Many2one(
        "trasas.dispatch.outgoing",
        string="Công văn",
        required=True,
    )
    reason = fields.Text(
        string="Lý do từ chối",
        required=True,
    )

    def action_reject(self):
        self.ensure_one()
        dispatch = self.dispatch_id

        # Add reason as note
        note_msg = f"<b>Lý do từ chối:</b><br/>{self.reason}"
        dispatch.message_post(body=note_msg)

        # Cập nhật note (ghi chú chung) nếu muốn
        if dispatch.note:
            dispatch.note = f"{dispatch.note}\n\nLý do từ chối: {self.reason}"
        else:
            dispatch.note = f"Lý do từ chối: {self.reason}"

        stage_draft = dispatch._get_stage("outgoing_stage_draft")
        if not stage_draft:
            stage_draft = dispatch.env["trasas.dispatch.outgoing.stage"].search(
                [("is_draft", "=", True)], limit=1
            )

        if stage_draft:
            # Cancel activity when rejected
            activity_type_id = self.env.ref(
                "mail.mail_activity_data_todo", raise_if_not_found=False
            )
            if activity_type_id:
                dispatch.activity_ids.filtered(
                    lambda a: (
                        a.activity_type_id.id == activity_type_id.id
                        and a.user_id.id == dispatch.approver_id.id
                    )
                ).unlink()

            # Gửi email template "Bị từ chối"
            template = self.env.ref(
                "trasas_dispatch_outgoing.email_template_outgoing_rejected",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(dispatch.id, force_send=True)

            dispatch.stage_id = stage_draft
