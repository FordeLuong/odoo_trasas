# -*- coding: utf-8 -*-
{
    "name": "TRASAS Contract Management",
    "version": "19.0.1.0.0",
    "category": "Contract Management",
    "summary": "Quản lý hợp đồng TRASAS - Từ soạn thảo đến ký kết và theo dõi",
    "description": """
        Hệ thống Quản lý Hợp đồng TRASAS
        ================================
        
        Tính năng chính:
        - Quản lý vòng đời hợp đồng từ Draft → Signed
        - Quy trình phê duyệt đa cấp
        - Luồng ký linh hoạt (TRASAS ký trước / Đối tác ký trước)
        - Thông báo tự động về hạn ký và hạn hợp đồng
        - Quản lý file PDF và bản scan
        - Báo cáo và tra cứu nâng cao
        - Tích hợp Chatter để trao đổi nội bộ
        
        Quy trình:
        1. Nhân viên tạo hợp đồng (Draft)
        2. Gửi duyệt (Waiting)
        3. Giám đốc phê duyệt (Approved)
        4. Tiến hành ký kết (Signing)
        5. Hoàn tất ký kết (Signed)
        6. HCNS đóng dấu và upload bản scan cuối cùng
        7. Hệ thống tự động nhắc nhở khi sắp hết hạn
    """,
    "author": "TRASAS",
    "website": "https://trasas.com",
    "depends": [
        "base",
        "mail",  # Để có Chatter và gửi email
        "contacts",  # Để quản lý đối tác
        "sign",  # Tích hợp chữ ký số
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "data/contract_type_data.xml",
        "data/contract_stage_data.xml",
        # Views
        "views/contract_type_views.xml",
        "views/contract_stage_views.xml",
        "views/contract_appendix_views.xml",
        "views/contract_views.xml",
        "views/contract_reject_wizard_views.xml",
        "views/menu_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
    "post_init_hook": "_assign_stages_to_existing_contracts",
}
