# -*- coding: utf-8 -*-
{
    "name": "TRASAS Digital Signature",
    "version": "19.0.1.0.0",
    "category": "Contract Management",
    "summary": "Chữ ký số - Tích hợp API nhà cung cấp chữ ký số cho hợp đồng TRASAS",
    "description": """
        Hệ thống Chữ ký số TRASAS
        ==========================

        Tính năng chính:
        - Tích hợp API nhà cung cấp chữ ký số (configurable provider)
        - Nhà cung cấp: VNPT-CA
        - Luồng ký linh hoạt: TRASAS ký trước hoặc Đối tác ký trước
        - Tự động gửi email mời ký kèm link
        - Webhook callback nhận kết quả ký từ nhà cung cấp
        - Cron kiểm tra trạng thái định kỳ (fallback)
        - Nhà cung cấp Demo tích hợp sẵn để test
    """,
    "author": "TRASAS",
    "website": "https://trasas.com",
    "depends": [
        "base",
        "mail",
        "trasas_contract_management",
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "data/mail_template_data.xml",
        "data/signature_provider_data.xml",
        # Views
        "views/signature_provider_views.xml",
        "views/signature_request_views.xml",
        "views/signature_api_log_views.xml",
        "views/contract_views.xml",
        "views/menu_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
