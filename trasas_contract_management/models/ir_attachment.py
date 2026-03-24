# -*- coding: utf-8 -*-
from odoo import models, api

import logging
_logger = logging.getLogger(__name__)

class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.res_model == "trasas.contract" and record.res_id:
                _logger.info("Auto-syncing attachment %s to contract %s (Create)", record.id, record.res_id)
                contract = self.env["trasas.contract"].browse(record.res_id)
                if contract.exists():
                    contract.sudo()._sync_attachments_to_document()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ["res_model", "res_id", "datas", "name"]):
            for record in self:
                if record.res_model == "trasas.contract" and record.res_id:
                    _logger.info("Auto-syncing attachment %s to contract %s (Write: %s)", record.id, record.res_id, list(vals.keys()))
                    contract = self.env["trasas.contract"].browse(record.res_id)
                    if contract.exists():
                        contract.sudo()._sync_attachments_to_document()
        return res
