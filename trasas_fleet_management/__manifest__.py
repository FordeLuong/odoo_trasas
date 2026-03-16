# -*- coding: utf-8 -*-
{
    "name": "TRASAS Fleet Management",
    "version": "19.0.1.0.0",
    "category": "Fleet",
    "summary": "Quản lý phương tiện nội bộ",
    "description": """
        Hệ thống Quản lý Phương tiện
        ====================================

        Tính năng chính:
        - Cấp mã phương tiện tự động: STT.YY/PT-TRS
        - Quản lý trạng thái xe: Mới, Sẵn sàng, Đang sử dụng, Bảo dưỡng, Sửa chữa, Thanh lý
        - Cảnh báo đăng kiểm, bảo hiểm, bảo trì (30-15-7 ngày)
        - Quản lý hồ sơ pháp lý đính kèm xe
        - Tích hợp Documents để lưu trữ chứng từ
        - Kế thừa và mở rộng module fleet chuẩn Odoo
    """,
    "author": "LiemPhong",
    "website": "https://www.psmerp.vn",
    "depends": ["fleet", "mail", "documents"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Data
        "data/ir_sequence_data.xml",
        "data/fleet_vehicle_state_data.xml",
        "data/ir_cron_data.xml",
        "data/fleet_service_type_data.xml",
        "data/fleet_config_data.xml",
        # Views
        "views/fleet_config_views.xml",
        "views/fleet_vehicle_views.xml",
        "views/fleet_legal_document_views.xml",
        "views/fleet_service_log_views.xml",
        "views/fleet_vehicle_report_views.xml",
        "views/menu_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
    "post_init_hook": "_post_init_trasas_fleet_states",
}
