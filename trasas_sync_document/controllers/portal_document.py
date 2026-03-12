# -*- coding: utf-8 -*-
import base64
from werkzeug.urls import url_quote
from odoo import http, fields
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

    def _check_portal_access(self, document):
        """Kiểm tra portal user có quyền truy cập vào document restricted không.
        Trả về True nếu user đã được cấp quyền qua documents.access.
        """
        partner = request.env.user.partner_id
        if not partner:
            return False

        access = request.env["documents.access"].sudo().search(
            [
                ("document_id", "=", document.id),
                ("partner_id", "=", partner.id),
            ],
            limit=1,
        )
        if not access:
            return False

        # Kiểm tra hết hạn
        if access.expiration_date and access.expiration_date < fields.Datetime.now():
            return False

        return True

    def _check_pending_request(self, document_ids):
        """Kiểm tra xem portal user đã có yêu cầu pending cho document này chưa.
        Trả về set document IDs đã có yêu cầu chưa xử lý.
        """
        if not document_ids:
            return set()
        pending = request.env["trasas.doc.access.request"].sudo().search(
            [
                ("user_id", "=", request.env.user.id),
                ("state", "in", ["draft", "submitted"]),
                ("document_ids", "in", document_ids),
            ]
        )
        pending_doc_ids = set()
        for req in pending:
            for doc in req.document_ids:
                if doc.id in document_ids:
                    pending_doc_ids.add(doc.id)
        return pending_doc_ids

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

        # Lấy files trong thư mục hiện tại (public + restricted, ẩn "only me")
        files = Document.search(
            [
                ("folder_id", "=", current_folder.id),
                ("type", "in", ["binary", "url"]),
                ("active", "=", True),
                ("confidential_level", "in", ["public", "restricted"]),
            ],
            order="sequence, name",
        )

        # Kiểm tra yêu cầu đang chờ
        restricted_ids = [f.id for f in files if f.confidential_level == "restricted"]
        pending_request_ids = self._check_pending_request(restricted_ids)

        # Chuẩn bị dữ liệu file với icon và format size
        file_list = []
        for f in files:
            is_restricted = f.confidential_level == "restricted"
            has_access = False
            has_pending = False

            if is_restricted:
                has_access = self._check_portal_access(f)
                has_pending = f.id in pending_request_ids

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
                    "is_restricted": is_restricted,
                    "has_access": has_access,
                    "has_pending": has_pending,
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

        # Kiểm tra quyền cho file restricted
        if document.confidential_level == "restricted":
            if not self._check_portal_access(document):
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

        # Kiểm tra quyền cho file restricted
        if document.confidential_level == "restricted":
            if not self._check_portal_access(document):
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

    # =========================================================================
    # PORTAL ACCESS REQUEST
    # =========================================================================

    @http.route(
        "/my/documents/request-access",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_request_access(self, **kw):
        """Portal user gửi yêu cầu truy cập tài liệu restricted."""
        import logging
        _logger = logging.getLogger(__name__)

        document_id = int(kw.get("document_id", 0))
        purpose = kw.get("purpose", "").strip()
        redirect_url = kw.get("redirect_url", "/my/documents")

        if not document_id or not purpose:
            return request.redirect(redirect_url)

        try:
            Document = request.env["documents.document"].sudo()
            document = Document.browse(document_id)
            root = self._get_root_workspace()

            if (
                not document.exists()
                or document.confidential_level != "restricted"
                or not self._is_descendant_of(document, root)
            ):
                return request.redirect(redirect_url)

            # Kiểm tra đã có yêu cầu pending chưa
            AccessRequest = request.env["trasas.doc.access.request"].sudo()
            existing = AccessRequest.search(
                [
                    ("user_id", "=", request.env.user.id),
                    ("state", "in", ["draft", "submitted"]),
                    ("document_ids", "in", [document_id]),
                ],
                limit=1,
            )
            if existing:
                return request.redirect(redirect_url)

            # Tạo yêu cầu mới (state=draft trước, rồi chuyển submitted)
            access_req = AccessRequest.create(
                {
                    "user_id": request.env.user.id,
                    "document_ids": [(6, 0, [document_id])],
                    "purpose": purpose,
                    "access_type": "view",
                    "access_duration": "7",
                    "is_portal_request": True,
                }
            )

            # Chuyển state sang submitted
            access_req.write({"state": "submitted"})

            # Gửi thông báo cho HCNS Manager
            try:
                manager_group = request.env.ref(
                    "trasas_document_management.group_doc_manager",
                    raise_if_not_found=False,
                )
                if manager_group:
                    manager_group = manager_group.sudo()
                    manager_users = manager_group.user_ids if hasattr(manager_group, 'user_ids') else manager_group.users
                    for mgr_user in manager_users:
                        access_req.activity_schedule(
                            "mail.mail_activity_data_todo",
                            user_id=mgr_user.id,
                            summary="Yêu cầu truy cập từ Portal: %s" % access_req.name,
                            note="Người dùng portal %s yêu cầu xem tài liệu '%s'. Mục đích: %s"
                            % (request.env.user.name, document.name, purpose),
                        )
                        _logger.info("Scheduled activity for user %s (id=%s)", mgr_user.name, mgr_user.id)
            except Exception as e:
                _logger.warning("Portal access request: Failed to schedule activity: %s", e, exc_info=True)

            try:
                access_req.message_post(
                    body="📤 Yêu cầu truy cập từ Portal đã được gửi, đang chờ HCNS phê duyệt.",
                    subject="Yêu cầu truy cập từ Portal",
                )
            except Exception as e:
                _logger.warning("Portal access request: Failed to post message: %s", e)

            _logger.info("Portal access request created: %s for document %s", access_req.name, document_id)

        except Exception as e:
            _logger.error("Portal access request failed: %s", e, exc_info=True)

        return request.redirect(redirect_url)

    @http.route(
        "/my/documents/my-requests",
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_requests(self, **kw):
        """Trang hiển thị danh sách yêu cầu truy cập của portal user."""
        requests_list = request.env["trasas.doc.access.request"].sudo().search(
            [("user_id", "=", request.env.user.id)],
            order="create_date desc",
        )

        state_labels = {
            "draft": "Nháp",
            "submitted": "Chờ duyệt",
            "approved": "Đã duyệt",
            "rejected": "Từ chối",
            "expired": "Hết hạn",
        }

        state_badges = {
            "draft": "bg-secondary",
            "submitted": "bg-warning text-dark",
            "approved": "bg-success",
            "rejected": "bg-danger",
            "expired": "bg-dark",
        }

        req_list = []
        for r in requests_list:
            doc_names = ", ".join(r.document_ids.mapped("name"))
            req_list.append(
                {
                    "name": r.name,
                    "documents": doc_names,
                    "purpose": r.purpose,
                    "state": r.state,
                    "state_label": state_labels.get(r.state, r.state),
                    "state_badge": state_badges.get(r.state, "bg-secondary"),
                    "create_date": r.create_date,
                    "access_expiry_date": r.access_expiry_date,
                }
            )

        values = {
            "requests": req_list,
            "page_name": "doc_requests",
        }
        return request.render("trasas_sync_document.portal_my_requests_page", values)
