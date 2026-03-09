{
    "name": "Portal TRASAS",
    "version": "1.3",
    "summary": "TRASAS Portal - Giao diện Portal cho nhân viên",
    "description": """
        Module mở rộng Portal chuẩn Odoo với giao diện social media.
        Bao gồm ứng dụng phê duyệt cho portal users.
    """,
    "category": "Website/Website",
    "author": "LiemPhong",
    "depends": ["portal", "website_blog", "website_slides", "hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/portal_templates.xml",
        "views/portal_management.xml",
        "data/blog_config.xml",
        "data/demo_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "portal_trasas/static/src/js/portal_approvals.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
