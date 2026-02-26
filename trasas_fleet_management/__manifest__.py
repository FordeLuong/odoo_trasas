# -*- coding: utf-8 -*-
{
    "name": "TRASAS Fleet Management",
    "version": "1.0",
    "summary": "Quản lý phương tiện TRASAS",
    "description": """
        Kế thừa module fleet để quản lý thông tin phương tiện nội bộ:
        - Cấp mã phương tiện tự động STT.YY/PT-TRS
        - Quản lý trạng thái xe: Mới, Sẵn sàng, Đang sử dụng, Bảo dưỡng, Sửa chữa...
        - Cảnh báo đăng kiểm, bảo hiểm, bảo trì 30-15-7 ngày.
        - Quản lý hồ sơ pháp lý đính kèm xe.
    """,
    "author": "TRASAS",
    "category": "Fleet",
    "depends": ["fleet", "mail", "documents"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/fleet_vehicle_state_data.xml",
        "data/ir_cron_data.xml",
        "data/fleet_service_type_data.xml",
        "views/fleet_vehicle_views.xml",
        "views/fleet_legal_document_views.xml",
        "views/fleet_service_log_views.xml",
    ],
    "post_init_hook": "_post_init_trasas_fleet_states",
    "installable": True,
    "application": True,
    "license": "OEEL-1",
}
