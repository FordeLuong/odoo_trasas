# -*- coding: utf-8 -*-
{
    "name": "TRASAS Fleet Demo Data",
    "version": "19.0.1.0.0",
    "category": "Fleet",
    "summary": "Dữ liệu mẫu hãng xe và model xe cho Fleet",
    "description": """
        TRASAS Fleet Demo Data
        ======================

        Tính năng chính:
        - Tạo sẵn các hãng xe và model xe phổ biến tại Việt Nam
        - Toyota, Hyundai, Kia, Ford, Mitsubishi, Isuzu, Hino, Thaco
        - Các dòng xe tải, xe khách, xe con thông dụng
        - Dùng để test và demo module Fleet TRASAS
    """,
    "author": "LiemPhong",
    "website": "https://www.psmerp.vn",
    "depends": ["fleet"],
    "data": [
        # Data
        "data/fleet_brand_data.xml",
        "data/fleet_model_data.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
