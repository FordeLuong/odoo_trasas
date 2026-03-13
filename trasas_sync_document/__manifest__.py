# -*- coding: utf-8 -*-
{
    "name": "TRASAS - Portal Documents Sync",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "summary": "Hiển thị tài liệu nội bộ trên Portal (chỉ xem và tải xuống)",
    "description": """
        TRASAS Portal Documents Sync
        ============================

        Tính năng chính:
        - Đồng bộ tài liệu nội bộ từ Documents lên Portal
        - Nhân viên xem và tải tài liệu được phân quyền
        - Không cho phép chỉnh sửa qua Portal
        - Tích hợp với module trasas_document_management
    """,
    "author": "LiemPhong",
    "website": "https://www.psmerp.vn",
    "depends": ["portal", "documents", "trasas_document_management", "website"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/portal_document_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "trasas_sync_document/static/src/css/portal_documents.css",
            "trasas_sync_document/static/src/js/portal_documents.js",
        ],
    },
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
