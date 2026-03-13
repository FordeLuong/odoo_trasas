# -*- coding: utf-8 -*-
{
    "name": "TRASAS Asset Management",
    "version": "19.0.2.0.0",
    "category": "Asset Management",
    "summary": "Quản lý thông tin tài sản TRASAS — Nhà cửa, máy móc, TBVP, vô hình",
    "description": """
        Hệ thống Quản lý Thông tin Tài sản TRASAS
        ==========================================

        Tính năng chính:
        - 4 nhóm tài sản: Nhà cửa/CT, Máy móc, TB Văn phòng, Vô hình
        - Mã tự động: STT.YY/TS-NHÓM-TRS
        - 5 trạng thái: Nháp → Đang sử dụng → Bảo trì / Hư hỏng / Thanh lý
        - Trường riêng conditional theo nhóm tài sản
        - Kế toán: TK tài sản, khấu hao, chi phí, nhật ký
        - Hồ sơ chứng từ đính kèm (notebook lines)
        - Cảnh báo hết hạn (Cron + Email + Activity)
        - Phân quyền HCNS (toàn quyền) / BGĐ (chỉ xem)
    """,
    "author": "LiemPhong",
    "website": "https://www.psmerp.vn",
    "depends": [
        "base",
        "mail",
        "hr",
        "account",
        "documents",
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/mail_template_data.xml",
        "data/ir_sequence_data.xml",
        "data/document_workspace_data.xml",
        "data/asset_type_data.xml",
        "data/asset_document_type_data.xml",
        "data/asset_stage_data.xml",
        "data/ir_cron_data.xml",
        # Wizard
        "wizard/asset_contract_wizard_views.xml",
        "wizard/asset_renew_wizard_views.xml",
        "wizard/asset_renovation_wizard_views.xml",
        "wizard/asset_repair_wizard_views.xml",
        "wizard/asset_reuse_wizard_views.xml",
        # Views
        "views/asset_legal_document_views.xml",
        "views/asset_config_views.xml",
        "views/asset_type_views.xml",
        "views/asset_views.xml",
        "views/menu_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
