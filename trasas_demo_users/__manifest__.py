# -*- coding: utf-8 -*-
{
    "name": "TRASAS Demo Users",
    "version": "19.0.2.0.0",
    "category": "Human Resources",
    "summary": "Demo users và employees cho test phân quyền TRASAS",
    "description": """
        Module Demo Users cho TRASAS
        ============================

        Module này tạo sẵn 5 nhân viên, 4 phòng ban và 5 user tương ứng để test phân quyền:

        PHÒNG BAN:
        1. Ban Giám đốc
        2. Phòng Hành chính nhân sự (HCNS)
        3. Phòng Vận hành
        4. Phòng Tài chính kế toán

        NHÂN VIÊN & TÀI KHOẢN:
        1. Trần Văn Minh - Giám đốc | giamdoc@trasas.com | trasas2026 | Contract Approver
        2. Nguyễn Thị Lan - Trưởng phòng HCNS | hcns.truong@trasas.com | trasas2026 | Contract Manager
        3. Phạm Văn Hùng - Nhân viên HCNS | hcns.nv@trasas.com | trasas2026 | Contract User
        4. Lê Thị Mai - Nhân viên Vận hành | vanhanh@trasas.com | trasas2026 | Contract User
        5. Hoàng Văn Nam - Nhân viên Kế toán | ketoan@trasas.com | trasas2026 | Contract User
    """,
    "author": "LiemPhong",
    "website": "https://www.psmerp.vn",
    "depends": [
        "base",
        "hr",
        "trasas_contract_management",
    ],
    "data": [
        # Data
        "data/hr_department_data.xml",
        "data/hr_employee_data.xml",
        "data/res_users_data.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
