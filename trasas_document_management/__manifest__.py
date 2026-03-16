# -*- coding: utf-8 -*-
{
    "name": "TRASAS Quản lý hồ sơ, tài liệu",
    "version": "19.0.1.1.0",
    "category": "Document Management",
    "summary": "Quản lý hồ sơ, tài liệu nội bộ với quy trình phê duyệt và phần quyền truy cập",
    "description": """
        Hệ thống Quản lý Hồ sơ 
        ====================================================

        Tính năng chính:
        - Quản lý tài liệu, phiên bản,...
        - Quy trình yêu cầu truy cập có giới hạn thời gian
        - Phê duyệt truy cập trực tiếp đa cấp bậc
        - Tự động cảnh báo tài liệu sắp hết hiệu lực
        - Thu hồi văn bản hết hiệu lực và thông báo phòng ban
        - Ghi nhận lịch sử truy cập
        - Báo cáo ISO
    """,
    "author": "LiemPhong",
    "website": "https://www.psmerp.vn",
    "license": "LGPL-3",
    "depends": [
        "documents",
        "mail",
        "hr",
    ],
    "data": [
        # Security
        "security/security_groups.xml",
        "security/ir_rules.xml",
        "security/ir.model.access.csv",
        # Data
        "data/ir_cron_data.xml",
        "data/document_workspace_data.xml",
        # Views
        "views/document_views.xml",
        "views/access_request_views.xml",
        "views/access_log_views.xml",
        "views/menu_views.xml",
        # Reports
        "report/doc_iso_report.xml",
        "views/report_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "trasas_document_management/static/src/views/inspector/confidential_level_field.js",
            "trasas_document_management/static/src/views/inspector/documents_details_panel_patch.js",
            "trasas_document_management/static/src/views/inspector/documents_details_panel_trasas.xml",
        ],
    },
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
