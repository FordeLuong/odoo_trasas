# -*- coding: utf-8 -*-
from odoo import models, fields


class TrasasDocReportWizard(models.TransientModel):
    """Wizard xuất Báo cáo ISO — Sổ Kiểm Soát Tài Liệu (B6)"""

    _name = "trasas.doc.report.wizard"
    _description = "Wizard Báo cáo ISO"

    folder_id = fields.Many2one(
        "documents.document",
        string="Workspace",
        domain="[('type', '=', 'folder')]",
    )

    document_type_id = fields.Many2one(
        "trasas.document.type",
        string="Loại hồ sơ",
    )

    doc_state = fields.Selection(
        [
            ("all", "Tất cả"),
            ("active", "Hiệu lực"),
            ("expiring_soon", "Sắp hết hạn"),
            ("expired", "Hết hiệu lực"),
            ("revoked", "Đã thu hồi"),
        ],
        string="Trạng thái",
        default="all",
    )

    date_from = fields.Date(string="Từ ngày")
    date_to = fields.Date(string="Đến ngày")

    def _build_domain(self):
        """Xây dựng domain tìm kiếm tài liệu dựa trên bộ lọc."""
        domain = [("type", "!=", "folder")]
        if self.folder_id:
            # child_of: lấy file trong folder này + tất cả sub-folder
            domain.append(("folder_id", "child_of", self.folder_id.id))
        if self.document_type_id:
            domain.append(("document_type_id", "=", self.document_type_id.id))
        if self.doc_state and self.doc_state != "all":
            domain.append(("doc_state", "=", self.doc_state))
        if self.date_from:
            domain.append(("issue_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("issue_date", "<=", self.date_to))
        return domain

    def action_print(self):
        """Xuất báo cáo PDF."""
        self.ensure_one()
        domain = self._build_domain()
        # sudo(): báo cáo ISO cần thấy tất cả tài liệu bất kể access_internal
        documents = (
            self.env["documents.document"]
            .sudo()
            .search(domain, order="document_type_id, document_number, name")
        )
        data = {
            "doc_ids": documents.ids,
            "wizard": {
                "folder_name": self.folder_id.name or "Tất cả",
                "document_type_name": self.document_type_id.name or "Tất cả",
                "doc_state": dict(self._fields["doc_state"].selection).get(
                    self.doc_state, "Tất cả"
                ),
                "date_from": self.date_from.strftime("%d/%m/%Y")
                if self.date_from
                else "",
                "date_to": self.date_to.strftime("%d/%m/%Y") if self.date_to else "",
            },
        }
        return self.env.ref(
            "trasas_document_management.action_report_doc_iso"
        ).report_action(documents, data=data)
