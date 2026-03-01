# -*- coding: utf-8 -*-
import requests
from odoo import _
from odoo.exceptions import UserError

class SmartCAClient:
    def __init__(self, env):
        self.env = env
        ICP = env["ir.config_parameter"].sudo()
        self.base_url = (ICP.get_param("vnpt_smartca.base_url") or "").rstrip("/")
        self.sp_id = ICP.get_param("vnpt_smartca.sp_id")
        self.sp_password = ICP.get_param("vnpt_smartca.sp_password")
        self.timeout = int(ICP.get_param("vnpt_smartca.timeout") or 30)

        if not (self.base_url and self.sp_id and self.sp_password):
            raise UserError(_("Please configure VNPT SmartCA (Base URL, SP ID, SP Password)."))

    def _post(self, path, payload):
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            raise UserError(_("SmartCA request failed: %s") % (e,))

        if data.get("status_code") and data.get("status_code") != 200:
            raise UserError(_("SmartCA error: %s") % (data.get("message") or data))
        return data

    def get_certificates(self, user_id, transaction_id):
        payload = {
            "sp_id": self.sp_id,
            "sp_password": self.sp_password,
            "user_id": user_id,
            "serial_number": "",
            "transaction_id": transaction_id,
        }
        return self._post("v1/credentials/get_certificate", payload)

    def sign_v1(self, user_id, transaction_id, transaction_desc, serial_number, time_stamp, sign_files):
        payload = {
            "sp_id": self.sp_id,
            "sp_password": self.sp_password,
            "user_id": user_id,
            "transaction_desc": transaction_desc or "",
            "transaction_id": transaction_id,
            "serial_number": serial_number,
            "time_stamp": time_stamp,
            "sign_files": sign_files,
        }
        return self._post("v1/signatures/sign", payload)

    def sign_status(self, transaction_id):
        # Some deployments accept empty body {}
        return self._post(f"v1/signatures/sign/{transaction_id}/status", {})