# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

# Initialize Odoo
odoo.tools.config.parse_config(["-c", "d:/Tech/odoo-19.0+e.20250918/odoo.conf"])

# Connect to database
db_name = "odooMCD"
registry = odoo.registry(db_name)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Search for all mail templates related to outgoing dispatch
    templates = env["mail.template"].search(
        [("model", "=", "trasas.dispatch.outgoing")]
    )

    for template in templates:
        updated = False

        # Fix subject
        if template.subject and "object.dispatch_number" in template.subject:
            template.subject = template.subject.replace(
                "object.dispatch_number", "object.name"
            )
            updated = True

        # Fix body
        if template.body_html and "object.dispatch_number" in template.body_html:
            template.body_html = template.body_html.replace(
                "object.dispatch_number", "object.name"
            )
            updated = True

        if updated:
            print(f"Fixed template: {template.name} ({template.id})")

    # Commit changes
    cr.commit()
    print("Done fixing mail templates.")
