# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Chạy logic cập nhật folder visibility khi upgrade lên 19.0.1.1.0"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.trasas_document_management.hooks import post_migrate

    post_migrate(env)
