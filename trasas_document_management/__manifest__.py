# -*- coding: utf-8 -*-
{
    "name": "TRASAS - Quản lý Hồ sơ & Tài liệu (DMS)",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "summary": "Quản lý hồ sơ, tài liệu nội bộ với quy trình phê duyệt và truy cập có giới hạn",
    "description": """
        Module Quản lý Hồ sơ TRASAS cho Odoo 19 Enterprise
        ====================================================
        
        Tính năng:
        * Kế thừa Documents Enterprise - tận dụng Workspace, Upload, Phiên bản
        * Bổ sung thông tin cơ bản trên tài liệu (Loại chứng từ, Ngày cấp, Hiệu lực...)
        * Quy trình yêu cầu truy cập có giới hạn thời gian
        * Phê duyệt truy cập bởi HCNS
        * BGĐ truy cập trực tiếp - bypass phê duyệt
        * Tự động cảnh báo tài liệu sắp hết hiệu lực
        * Thu hồi văn bản hết hiệu lực + thông báo phòng ban
        * Ghi nhận lịch sử truy cập (Audit Trail)
        * Báo cáo ISO (Danh mục hiệu lực, Ma trận phân phối, LS truy cập)
    """,
    "author": "TRASAS",
    "website": "https://www.trasas.vn",
    "license": "LGPL-3",
    "depends": [
        "documents",
        "mail",
        "hr",
    ],
    "data": [
        "security/security_groups.xml",
        "security/ir_rules.xml",
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/document_views.xml",
        "views/access_request_views.xml",
        "views/access_log_views.xml",
        "views/menu_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
