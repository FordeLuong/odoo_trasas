# -*- coding: utf-8 -*-
{
    "name": "TRASAS Dispatch Management",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "summary": "Quản lý công văn đến và đi",
    "description": """
        Hệ thống Quản lý Công văn TRASAS
        ================================
        Quản lý toàn bộ quy trình công văn đến từ tiếp nhận, phân loại,
        chỉ đạo, xử lý cho đến lưu trữ.
    """,
    "author": "TRASAS",
    "depends": ["base", "mail", "contacts", "portal", "portal_custom"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/dispatch_data.xml",
        "data/dispatch_stage_data.xml",
        "data/ir_cron_data.xml",
        "data/mail_template_data.xml",
        "views/dispatch_stage_views.xml",
        "views/dispatch_incoming_views.xml",
        "views/dispatch_type_views.xml",
        "views/menu_views.xml",
        "views/portal_templates.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
    "post_init_hook": "_assign_stages_to_existing",
}
