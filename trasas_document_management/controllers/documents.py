# -*- coding: utf-8 -*-
from http import HTTPStatus

from odoo import http
from odoo.http import request, Response

from odoo.addons.documents.controllers.documents import ShareRoute


class TrasasShareRoute(ShareRoute):
    """Override Documents controller để chặn nội dung file Giới hạn
    cho user chưa được cấp quyền truy cập.
    """

    @http.route('/documents/content/<access_token>',
                type='http', auth='public', readonly=True)
    def documents_content(self, access_token, download=True):
        """Chặn tải/xem nội dung file nếu user chưa có quyền truy cập."""
        document_sudo = self._from_access_token(access_token, skip_log=True)
        if document_sudo and document_sudo.type == 'binary':
            # Kiểm tra can_access_content với user hiện tại (không sudo)
            if not request.env.user._is_public():
                doc_as_user = request.env['documents.document'].browse(document_sudo.id)
                try:
                    can_access = doc_as_user.can_access_content
                except Exception:
                    can_access = True  # Fallback: cho phép nếu có lỗi
                if not can_access:
                    return Response(
                        "Tài liệu này ở chế độ Giới hạn. "
                        "Vui lòng xin quyền truy cập từ chủ sở hữu.",
                        status=HTTPStatus.FORBIDDEN,
                    )
        return super().documents_content(access_token, download=download)

    @http.route(['/documents/thumbnail/<access_token>',
                 '/documents/thumbnail/<access_token>/<int:width>x<int:height>'],
                type='http', auth='public', readonly=True)
    def documents_thumbnail(self, access_token, width='0', height='0', unique=''):
        """Chặn thumbnail nếu user chưa có quyền truy cập."""
        document_sudo = self._from_access_token(access_token, skip_log=True)
        if document_sudo and document_sudo.type == 'binary':
            if not request.env.user._is_public():
                doc_as_user = request.env['documents.document'].browse(document_sudo.id)
                try:
                    can_access = doc_as_user.can_access_content
                except Exception:
                    can_access = True
                if not can_access:
                    return Response(
                        "",
                        status=HTTPStatus.FORBIDDEN,
                    )
        return super().documents_thumbnail(
            access_token, width=width, height=height, unique=unique
        )
