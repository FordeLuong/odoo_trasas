# -*- coding: utf-8 -*-
{
    "name": "TRASAS Fleet Demo Data",
    "version": "1.0",
    "summary": "Dữ liệu mẫu hãng xe và model xe cho Fleet",
    "description": """
        Tạo sẵn các hãng xe và model xe phổ biến tại Việt Nam:
        - Toyota, Hyundai, Kia, Ford, Mitsubishi, Isuzu, Hino, Thaco
        - Các dòng xe tải, xe khách, xe con thông dụng
    """,
    "author": "TRASAS",
    "category": "Fleet",
    "depends": ["fleet"],
    "data": [
        "data/fleet_brand_data.xml",
        "data/fleet_model_data.xml",
    ],
    "installable": True,
    "application": False,
    "license": "OEEL-1",
}
