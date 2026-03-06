{
    "name": "TRASAS - Portal Documents Sync",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "summary": "Hiển thị tài liệu nội bộ trên Portal (chỉ xem và tải xuống)",
    "author": "LiemPhong",
    "depends": ["portal", "documents", "trasas_document_management", "website"],
    "data": [
        "security/ir.model.access.csv",
        "views/portal_document_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "trasas_sync_document/static/src/css/portal_documents.css",
            "trasas_sync_document/static/src/js/portal_documents.js",
        ],
    },
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
