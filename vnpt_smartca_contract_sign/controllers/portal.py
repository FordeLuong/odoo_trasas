# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class VnptContractPortal(CustomerPortal):

    @http.route(['/my/contracts/<int:contract_id>'], type='http', auth='public', website=True)
    def portal_contract(self, contract_id, access_token=None, **kw):
        Contract = request.env['vnpt.contract'].sudo()
        contract = Contract.browse(contract_id)
        contract.check_access_token(access_token)

        values = {"contract": contract, "access_token": access_token}
        return request.render("vnpt_smartca_contract_full.portal_contract_page", values)

    @http.route(['/my/contracts/<int:contract_id>/download/director-signed'], type='http', auth='public', website=True)
    def download_director_signed(self, contract_id, access_token=None, **kw):
        Contract = request.env['vnpt.contract'].sudo()
        contract = Contract.browse(contract_id)
        contract.check_access_token(access_token)

        att = contract.director_signed_attachment_id
        if not att:
            return request.not_found()

        content = att.raw if getattr(att, "raw", None) else (att.datas and base64.b64decode(att.datas) or b"")
        headers = [
            ('Content-Type', att.mimetype or 'application/pdf'),
            ('Content-Disposition', f'attachment; filename="{att.name or "contract.pdf"}"'),
        ]
        return request.make_response(content, headers=headers)

    @http.route(['/my/contracts/<int:contract_id>/upload/fully-signed'], type='http', auth='public', website=True, methods=['POST'])
    def upload_fully_signed(self, contract_id, access_token=None, **post):
        Contract = request.env['vnpt.contract'].sudo()
        contract = Contract.browse(contract_id)
        contract.check_access_token(access_token)

        file_storage = request.httprequest.files.get('fully_signed_file')
        if not file_storage or not file_storage.filename:
            return request.redirect(f"/my/contracts/{contract_id}?access_token={access_token}&upload=missing")

        data = file_storage.read()
        if not data:
            return request.redirect(f"/my/contracts/{contract_id}?access_token={access_token}&upload=empty")

        # basic check
        filename = file_storage.filename
        mimetype = file_storage.mimetype or "application/pdf"
        if "pdf" not in (mimetype or "").lower():
            # still allow but mark as issue in UI if you want
            pass

        att = request.env["ir.attachment"].sudo().create({
            "name": filename,
            "type": "binary",
            "mimetype": mimetype,
            "raw": data,
            "res_model": contract._name,
            "res_id": contract.id,
        })

        contract.sudo().write({
            "fully_signed_attachment_id": att.id,
            "state": "completed",
        })
        contract.sudo().message_post(body="Customer uploaded fully signed PDF. Contract completed.")

        return request.redirect(f"/my/contracts/{contract_id}?access_token={access_token}&upload=ok")