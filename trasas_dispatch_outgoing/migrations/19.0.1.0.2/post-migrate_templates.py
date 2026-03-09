# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """
    Migration script to fix `dispatch_number` -> `name` in mail templates.
    Uses ORM instead of raw SQL because subject and body_html are JSONB in Odoo 19.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Bỏ noupdate của bảng ir.model.data để Odoo ghi đè lại XML
    model_data = env["ir.model.data"].search(
        [
            ("module", "=", "trasas_dispatch_outgoing"),
            ("model", "=", "mail.template"),
        ]
    )
    if model_data:
        model_data.write({"noupdate": False})

    # Dùng ORM update để tự động xử lý JSONB đa ngôn ngữ thay vì raw SQL
    templates = env["mail.template"].search(
        [("model", "=", "trasas.dispatch.outgoing")]
    )
    for template in templates:
        vals = {}
        if template.subject and "dispatch_number" in template.subject:
            vals["subject"] = template.subject.replace("dispatch_number", "name")
        if template.body_html and "dispatch_number" in template.body_html:
            vals["body_html"] = template.body_html.replace("dispatch_number", "name")

        if vals:
            template.write(vals)
