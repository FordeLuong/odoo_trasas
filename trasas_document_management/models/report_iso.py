# -*- coding: utf-8 -*-
from odoo import api, models


class TrasasDocISOReport(models.AbstractModel):
    """Parser cho Báo cáo ISO — truyền dữ liệu từ wizard vào QWeb."""

    _name = "report.trasas_document_management.doc_iso_report_template"
    _description = "ISO Report Parser"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Lấy danh sách tài liệu theo bộ lọc từ wizard."""
        if data and data.get("doc_ids"):
            docs = self.env["documents.document"].sudo().browse(data["doc_ids"])
        elif docids:
            docs = self.env["documents.document"].sudo().browse(docids)
        else:
            docs = (
                self.env["documents.document"]
                .sudo()
                .search(
                    [("type", "!=", "folder")],
                    order="document_type_id, document_number, name",
                )
            )
        return {
            "doc_ids": docs.ids,
            "doc_model": "documents.document",
            "docs": docs,
            "data": data or {},
        }
