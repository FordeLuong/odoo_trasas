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
        
        **PHÒNG BAN:**
        1. Ban Giám đốc
        2. Phòng Hành chính nhân sự (HCNS)
        3. Phòng Vận hành
        4. Phòng Tài chính kế toán
        
        **NHÂN VIÊN & TÀI KHOẢN:**
        
        1. **Trần Văn Minh** - Giám đốc (Ban Giám đốc)
           - Email: giamdoc@trasas.com
           - Password: trasas2026
           - Quyền: Contract Approver
           - Vai trò: Phê duyệt hợp đồng, duyệt công văn, tra cứu tài sản
        
        2. **Nguyễn Thị Lan** - Trưởng phòng HCNS
           - Email: hcns.truong@trasas.com
           - Password: trasas2026
           - Quyền: Contract Manager
           - Vai trò: Quản lý công văn, hồ sơ, tài sản
        
        3. **Phạm Văn Hùng** - Nhân viên HCNS
           - Email: hcns.nv@trasas.com
           - Password: trasas2026
           - Quyền: Contract User
           - Vai trò: Xử lý công văn đến/đi, lưu trữ hồ sơ
        
        4. **Lê Thị Mai** - Nhân viên Vận hành
           - Email: vanhanh@trasas.com
           - Password: trasas2026
           - Quyền: Contract User
           - Vai trò: Tạo hồ sơ hợp đồng, lấy ý kiến, trình ký
        
        5. **Hoàng Văn Nam** - Nhân viên Kế toán
           - Email: ketoan@trasas.com
           - Password: trasas2026
           - Quyền: Contract User
           - Vai trò: Hỗ trợ báo cáo, audit
        
        Sau khi install module này, bạn có thể đăng nhập bằng các tài khoản trên
        để test quy trình quản lý hợp đồng và các quy trình vận hành khác.
    """,
    "author": "TRASAS",
    "website": "https://trasas.com",
    "depends": [
        "base",
        "hr",  # Để tạo employees và departments
        "trasas_contract_management",  # Để gán quyền
    ],
    "data": [
        "data/hr_department_data.xml",
        "data/hr_employee_data.xml",
        "data/res_users_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
