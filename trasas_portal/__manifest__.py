# -*- coding: utf-8 -*-
{
    "name": "TRASAS Portal",
    "version": "19.0.1.3.0",
    "category": "Website/Website",
    "summary": "Cổng thông tin cho nhân viên",
    "description": """
        Hệ thống Cổng thông tin
        =============

        Tính năng chính:
        - Mở rộng Portal chuẩn Odoo với giao diện social media
        - Giao diện phê duyệt dành cho portal users
        - Tích hợp blog, slides cho nội dung nội bộ
        - Kế thừa thông tin nhân viên từ module hr
    """,
    "author": "LiemPhong",
    "website": "https://www.psmerp.vn",
    "depends": ["portal", "website_blog", "website_slides", "hr"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/portal_templates.xml",
        "views/portal_management.xml",
        # Data
        "data/blog_config.xml",
        "data/demo_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "trasas_portal/static/src/js/portal_approvals.js",
        ],
    },
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
