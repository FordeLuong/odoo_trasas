# -*- coding: utf-8 -*-
from . import models


def _assign_stages_to_existing_contracts(env):
    """Gán stage cho các hợp đồng cũ dựa trên state hiện tại"""
    state_to_stage_xmlid = {
        "draft": "trasas_contract_management.stage_draft",
        "in_review": "trasas_contract_management.stage_in_review",
        "waiting": "trasas_contract_management.stage_waiting",
        "approved": "trasas_contract_management.stage_approved",
        "signing": "trasas_contract_management.stage_signing",
        "signed": "trasas_contract_management.stage_signed",
        "expired": "trasas_contract_management.stage_expired",
        "cancel": "trasas_contract_management.stage_cancel",
    }
    for state, xmlid in state_to_stage_xmlid.items():
        stage = env.ref(xmlid, raise_if_not_found=False)
        if stage:
            contracts = env["trasas.contract"].search(
                [
                    ("state", "=", state),
                    ("stage_id", "=", False),
                ]
            )
            if contracts:
                contracts.write({"stage_id": stage.id})
