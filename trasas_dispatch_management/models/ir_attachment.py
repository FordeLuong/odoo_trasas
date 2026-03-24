# -*- coding: utf-8 -*-
from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model_create_multi
    def create(self, vals_list):
        # Ưu tiên gán res_model/res_id từ context nếu widget M2M không gửi lên
        if self.env.context.get("default_res_model") in ["trasas.dispatch.incoming", "trasas.dispatch.outgoing"]:
            for vals in vals_list:
                if not vals.get("res_model"):
                    vals["res_model"] = self.env.context.get("default_res_model")
                if not vals.get("res_id") and self.env.context.get("default_res_id"):
                    vals["res_id"] = self.env.context.get("default_res_id")

        records = super(IrAttachment, self).create(vals_list)
        self._sync_dispatch_documents(records)
        return records

    def write(self, vals):
        # Chống loop đè
        if len(vals.keys()) == 2 and "res_model" in vals and "res_id" in vals:
            return super(IrAttachment, self).write(vals)
            
        res = super(IrAttachment, self).write(vals)
        if any(f in vals for f in ["datas", "name", "res_model", "res_id"]):
            self._sync_dispatch_documents(self)
        return res

    def _sync_dispatch_documents(self, attachments):
        """Trigger sync for Dispatch models"""
        dispatch_models = ["trasas.dispatch.incoming", "trasas.dispatch.outgoing"]
        for attachment in attachments:
            if attachment.res_model in dispatch_models and attachment.res_id:
                try:
                    record = self.env[attachment.res_model].sudo().browse(attachment.res_id)
                    if record.exists() and hasattr(record, "_sync_attachments_to_document"):
                        _logger.info(
                            "Auto-syncing attachment %s to %s ID %s",
                            attachment.name,
                            attachment.res_model,
                            attachment.res_id,
                        )
                        record._sync_attachments_to_document()
                except Exception as e:
                    _logger.error("Error auto-syncing dispatch attachment: %s", str(e))
