# -*- coding: utf-8 -*-
{
    "name": "TRASAS Dispatch Management",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "summary": "Quản lý công văn đến và đi",
    "description": """
        Hệ thống Quản lý Công văn
        ================================

        Tính năng chính:
        - Quản lý toàn bộ quy trình công văn đến
        - Tiếp nhận, phân loại, chỉ đạo, xử lý, lưu trữ
        - Tích hợp Portal để nhân viên theo dõi
        - Tích hợp Documents để lưu hồ sơ
        - Cảnh báo công văn chưa xử lý qua Cron
        - Email thông báo tự động theo giai đoạn
    """,
    "author": "LiemPhong",
    "website": "https://www.psmerp.vn",
    "depends": ["base", "mail", "contacts", "portal", "portal_trasas", "documents"],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/dispatch_data.xml",
        "data/dispatch_stage_data.xml",
        "data/dispatch_config_data.xml",
        "data/ir_cron_data.xml",
        "data/mail_template_data.xml",
        # Views
        "views/dispatch_config_views.xml",
        "views/dispatch_stage_views.xml",
        "views/dispatch_incoming_views.xml",
        "views/dispatch_type_views.xml",
        "views/menu_views.xml",
        "views/portal_templates.xml",
        # Data (post-views)
        "data/document_workspace_data.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
    "post_init_hook": "_assign_stages_to_existing",
}
