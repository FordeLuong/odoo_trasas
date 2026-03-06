# -*- coding: utf-8 -*-
import base64
from werkzeug.urls import url_quote
from odoo import http
from odoo.http import request


class PortalDocuments(http.Controller):
    def _get_root_workspace(self):
        """Lấy workspace gốc 'Hồ sơ tài liệu nội bộ'."""
        return request.env.ref(
            "trasas_document_management.workspace_trasas_internal_docs",
            raise_if_not_found=False,
        ).sudo()

    def _is_descendant_of(self, folder, root):
        """Kiểm tra folder có là con cháu của root không (bảo mật)."""
        current = folder
        while current:
            if current.id == root.id:
                return True
            current = current.folder_id
        return False

    def _get_folder_tree(self, parent_folder):
        """Đệ quy lấy cây thư mục con (chỉ type='folder')."""
        Document = request.env["documents.document"].sudo()
        folders = Document.search(
            [
                ("folder_id", "=", parent_folder.id),
                ("type", "=", "folder"),
                ("active", "=", True),
            ],
            order="sequence, name",
        )
        tree = []
        for folder in folders:
            tree.append(
                {
                    "id": folder.id,
                    "name": folder.name,
                    "children": self._get_folder_tree(folder),
                }
            )
        return tree

    def _get_breadcrumb(self, current_folder, root):
        """Tạo breadcrumb từ folder hiện tại về root."""
        breadcrumb = []
        parent = current_folder
        while parent and parent.id != root.id:
            breadcrumb.insert(0, {"id": parent.id, "name": parent.name})
            parent = parent.folder_id
        breadcrumb.insert(0, {"id": root.id, "name": root.name})
        return breadcrumb

    def _get_file_icon(self, document):
        """Trả về class icon FA tương ứng loại file."""
        mimetype = document.mimetype or ""
        ext = (document.file_extension or "").lower()
        if "pdf" in mimetype or ext == "pdf":
            return "fa fa-file-pdf-o text-danger"
        elif "image" in mimetype:
            return "fa fa-file-image-o text-info"
        elif "word" in mimetype or ext in ("doc", "docx"):
            return "fa fa-file-word-o text-primary"
        elif "excel" in mimetype or "spreadsheet" in mimetype or ext in ("xls", "xlsx"):
            return "fa fa-file-excel-o text-success"
        elif (
            "powerpoint" in mimetype
            or "presentation" in mimetype
            or ext in ("ppt", "pptx")
        ):
            return "fa fa-file-powerpoint-o text-warning"
        elif "text" in mimetype or ext == "txt":
            return "fa fa-file-text-o text-muted"
        elif "zip" in mimetype or "rar" in mimetype or ext in ("zip", "rar", "7z"):
            return "fa fa-file-archive-o text-secondary"
        elif document.type == "url":
            return "fa fa-link text-primary"
        return "fa fa-file-o text-muted"

    def _format_file_size(self, size_bytes):
        """Format kích thước file cho dễ đọc."""
        if not size_bytes:
            return "0 B"
        units = ["B", "KB", "MB", "GB"]
        unit_index = 0
        size = float(size_bytes)
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.1f} {units[unit_index]}"

    def _can_preview(self, document):
        """Kiểm tra file có hỗ trợ xem trước không."""
        mimetype = document.mimetype or ""
        return "pdf" in mimetype or "image" in mimetype

    @http.route(
        ["/my/documents", "/my/documents/<int:folder_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_documents(self, folder_id=None, **kw):
        root = self._get_root_workspace()
        if not root:
            return request.redirect("/my")

        Document = request.env["documents.document"].sudo()

        # Xác định thư mục hiện tại
        if folder_id:
            current_folder = Document.browse(folder_id)
            if not current_folder.exists() or not self._is_descendant_of(
                current_folder, root
            ):
                return request.redirect("/my/documents")
        else:
            current_folder = root

        # Lấy sub-folders trong thư mục hiện tại
        sub_folders = Document.search(
            [
                ("folder_id", "=", current_folder.id),
                ("type", "=", "folder"),
                ("active", "=", True),
            ],
            order="sequence, name",
        )

        # Lấy files trong thư mục hiện tại (chỉ tài liệu công khai)
        files = Document.search(
            [
                ("folder_id", "=", current_folder.id),
                ("type", "in", ["binary", "url"]),
                ("active", "=", True),
                ("confidential_level", "=", "public"),
            ],
            order="sequence, name",
        )

        # Chuẩn bị dữ liệu file với icon và format size
        file_list = []
        for f in files:
            file_list.append(
                {
                    "id": f.id,
                    "name": f.name or "Untitled",
                    "icon": self._get_file_icon(f),
                    "size": self._format_file_size(f.file_size),
                    "mimetype": f.mimetype or "",
                    "extension": (f.file_extension or "").upper(),
                    "can_preview": self._can_preview(f),
                    "type": f.type,
                    "url": f.url if f.type == "url" else False,
                }
            )

        # Cây thư mục và breadcrumb
        folder_tree = self._get_folder_tree(root)
        breadcrumb = self._get_breadcrumb(current_folder, root)

        values = {
            "root_folder": root,
            "current_folder": current_folder,
            "sub_folders": sub_folders,
            "files": file_list,
            "folder_tree": folder_tree,
            "breadcrumb": breadcrumb,
            "page_name": "documents",
        }
        return request.render("trasas_sync_document.portal_documents_page", values)

    @http.route(
        "/my/documents/download/<int:document_id>",
        type="http",
        auth="user",
        website=True,
    )
    def portal_document_download(self, document_id, **kw):
        root = self._get_root_workspace()
        if not root:
            return request.redirect("/my")

        document = request.env["documents.document"].sudo().browse(document_id)
        if (
            not document.exists()
            or document.type != "binary"
            or not document.datas
            or not self._is_descendant_of(document, root)
        ):
            return request.redirect("/my/documents")

        filename = document.name or "download"
        if document.file_extension and not filename.endswith(
            f".{document.file_extension}"
        ):
            filename = f"{filename}.{document.file_extension}"

        file_content = base64.b64decode(document.datas)

        return request.make_response(
            file_content,
            headers=[
                ("Content-Type", str(document.mimetype or "application/octet-stream")),
                (
                    "Content-Disposition",
                    f"attachment; filename*=UTF-8''{url_quote(filename)}",
                ),
                ("Content-Length", str(len(file_content))),
            ],
        )

    @http.route(
        "/my/documents/preview/<int:document_id>",
        type="http",
        auth="user",
        website=True,
    )
    def portal_document_preview(self, document_id, **kw):
        root = self._get_root_workspace()
        if not root:
            return request.redirect("/my")

        document = request.env["documents.document"].sudo().browse(document_id)
        if (
            not document.exists()
            or document.type != "binary"
            or not document.datas
            or not self._is_descendant_of(document, root)
            or not self._can_preview(document)
        ):
            return request.redirect("/my/documents")

        file_content = base64.b64decode(document.datas)
        filename = document.name or "preview"

        return request.make_response(
            file_content,
            headers=[
                ("Content-Type", str(document.mimetype or "application/octet-stream")),
                (
                    "Content-Disposition",
                    f"inline; filename*=UTF-8''{url_quote(filename)}",
                ),
                ("Content-Length", str(len(file_content))),
            ],
        )
