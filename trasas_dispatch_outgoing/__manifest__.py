# -*- coding: utf-8 -*-
{
    "name": "TRASAS Dispatch Outgoing",
    "version": "19.0.1.0.2",
    "category": "Document Management",
    "summary": "Module mở rộng: Quản lý Công văn đi",
    "description": """
        Hệ thống Quản lý Công văn Đi
        ====================================
        
        Tính năng chính:
        - Soạn thảo, trình ký công văn đi
        - Quản lý quy trình phê duyệt & ban hành
        - Luồng ký linh hoạt theo phân cấp
        - Lưu trữ và theo dõi trạng thái gửi
        - Tích hợp Portal để nhân viên xem công văn đã ban hành
        - Email thông báo tự động theo giai đoạn xử lý
    """,
    "author": "LiemPhong",
    "website": "https://www.psmerp.vn",
    "depends": [
        "base",
        "mail",
        "hr",
        "portal",
        "trasas_portal",
        "trasas_dispatch_management",
        "trasas_demo_users",
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/dispatch_data.xml",
        "data/dispatch_outgoing_stage_data.xml",
        "data/dispatch_config_data.xml",
        "data/mail_template_data.xml",
        # Wizard
        "wizard/dispatch_outgoing_reject_wizard_views.xml",
        # Views
        "views/dispatch_config_views.xml",
        "views/dispatch_outgoing_stage_views.xml",
        "views/dispatch_outgoing_views.xml",
        "views/dispatch_incoming_views_inherit.xml",
        "views/menu_views.xml",
        "views/portal_templates.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
    "post_init_hook": "_assign_outgoing_stages",
}
