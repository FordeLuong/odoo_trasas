# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import http
from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, _
from odoo.http import request
import time


class DocusignCode(http.Controller):
    @http.route("/docusign", auth="public", type='http')
    def fetch_code(self, **kwargs):
        try:
            if "error" in kwargs:
                ValidationError(kwargs['error'])
            if 'code' in kwargs:
                code = kwargs.get('code')
                rec = request.env.user
                rec.sudo().write({
                    'code': code
                })
                request.env.cr.commit()
                # request.env['res.users'].sudo().get_access_token(rec)
                return request.render("odoo_docusign.token_redirect_success_page")
            else:
                return request.render("odoo_docusign.token_redirect_fail_page")
        except Exception as e:
            raise ValidationError(_("Unable to fetch code and access token!"))

