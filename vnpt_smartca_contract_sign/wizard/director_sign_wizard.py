# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, timezone

from odoo import fields, models, _
from odoo.exceptions import UserError

from ..services.smartca_client import SmartCAClient
from ..services.pades_cms import PadesCms

class VnptDirectorSignWizard(models.TransientModel):
    _name = "vnpt.director.sign.wizard"
    _description = "VNPT Director Sign Wizard (No OTP in Odoo)"

    contract_id = fields.Many2one("vnpt.contract", required=True, ondelete="cascade")

    smartca_user_id = fields.Char(string="SmartCA User ID (CCCD/CMND/MST)", required=True)
    serial_number = fields.Char(string="Certificate serial", required=True)

    transaction_desc = fields.Char(string="transaction_desc", required=True)
    doc_id = fields.Char(string="doc_id (show on SmartCA app)", required=True)
    time_stamp = fields.Char(string="time_stamp (YYYYMMDDhhmmssZ)", required=True)

    def action_autofill(self):
        self.ensure_one()
        c = self.contract_id
        self.transaction_desc = f"Ky hop dong {c.name} - {c.partner_id.display_name}"
        self.doc_id = f"DOC-{c.id}-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)
        self.time_stamp = now.strftime("%Y%m%d%H%M%SZ")
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_send(self):
        self.ensure_one()
        c = self.contract_id
        if not c.unsigned_attachment_id:
            raise UserError(_("Missing Unsigned PDF attachment."))
        if c.state not in ("draft", "failed"):
            raise UserError(_("Contract not in a signable state."))

        original_pdf = c._get_unsigned_pdf_bytes()
        if not original_pdf:
            raise UserError(_("Unsigned PDF data empty."))

        # 1) prepare placeholder + tbs bytes for director signature
        pades = PadesCms()
        field_name = c.smartca_sig_field or "DirectorSignature1"
        prepared = pades.prepare_placeholder_and_tbs(
            original_pdf_bytes=original_pdf,
            field_name=field_name,
            reason=f"Director sign contract {c.name}",
            location="Odoo",
        )
        hash_hex = pades.tbs_sha256_hex_upper(prepared.bytes_to_sign)

        # 2) save placeholder attachment
        placeholder_att = self.env["ir.attachment"].create({
            "name": (c.unsigned_attachment_id.name or c.name) + " (director-placeholder).pdf",
            "type": "binary",
            "mimetype": "application/pdf",
            "raw": prepared.placeholder_pdf,
            "res_model": c._name,
            "res_id": c.id,
        })

        # 3) call SmartCA sign v1 (no OTP)
        client = SmartCAClient(self.env)
        tx_id = c.smartca_transaction_id or f"SP_CA_{uuid.uuid4().hex[:12].upper()}"

        sign_files = [{
            "doc_id": self.doc_id,
            "file_type": "pdf",
            "sign_type": "hash",
            "data_to_be_signed": hash_hex,
        }]

        resp = client.sign_v1(
            user_id=self.smartca_user_id,
            transaction_id=tx_id,
            transaction_desc=self.transaction_desc,
            serial_number=self.serial_number,
            time_stamp=self.time_stamp,
            sign_files=sign_files,
        )
        data = resp.get("data", {}) or {}

        c.write({
            "state": "waiting_director",
            "smartca_user_id": self.smartca_user_id,
            "smartca_serial_number": self.serial_number,
            "smartca_transaction_desc": self.transaction_desc,
            "smartca_doc_id": self.doc_id,
            "smartca_time_stamp": self.time_stamp,
            "smartca_transaction_id": data.get("transaction_id") or tx_id,
            "smartca_tran_code": data.get("tran_code"),
            "director_placeholder_attachment_id": placeholder_att.id,
        })

        c.message_post(body=_(
            "Sent VNPT SmartCA request to Director.<br/>"
            "Please confirm on SmartCA app.<br/>"
            "<b>doc_id</b>: %s<br/>"
            "<b>tran_code</b>: %s"
        ) % (self.doc_id, (data.get("tran_code") or "")))

        return {"type": "ir.actions.act_window_close"}