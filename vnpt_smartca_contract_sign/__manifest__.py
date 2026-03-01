# -*- coding: utf-8 -*-
{
    "name": "VNPT SmartCA - Contract Signing",
    "version": "19.0.1.0.0",
    "category": "Contract Management",
    "summary": "Tích hợp API chữ ký số của nhà cung cấp VNPT SmartCA (CMS/PAdES)",
     "description": """
        Hệ thống Chữ ký số VNPT SmartCA
        ==========================
        Tính năng chính:
        - Tích hợp API nhà cung cấp chữ ký số (VNPT SmartCA)
    """,
     "author": "TRASAS",
    "website": "https://trasas.com",
    "depends": ["base", "mail", "web", "portal", "website"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/contract_views.xml",
        "wizard/director_sign_wizard_views.xml",
        "views/portal_templates.xml",
        "data/mail_template.xml",
        "data/ir_cron.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}