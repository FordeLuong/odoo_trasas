# -*- coding: utf-8 -*-
{
    "name": "TRASAS Dispatch Outgoing",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "summary": "Module mở rộng: Quản lý Công văn đi",
    "description": """
        Mở rộng từ module Quản lý Công văn (trasas_dispatch_management).
        Tính năng:
        - Soạn thảo, trình ký công văn đi.
        - Quản lý quy trình phê duyệt & ban hành.
        - Lưu trữ và theo dõi trạng thái gửi.
    """,
    "author": "LiemPhong",
    "depends": [
        "base",
        "mail",
        "hr",
        "trasas_dispatch_management",
        "trasas_demo_users",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/dispatch_data.xml",
        "data/dispatch_outgoing_stage_data.xml",
        "data/mail_template_data.xml",
        "views/dispatch_outgoing_stage_views.xml",
        "views/dispatch_outgoing_views.xml",
        "views/menu_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
    "post_init_hook": "_assign_outgoing_stages",
}
