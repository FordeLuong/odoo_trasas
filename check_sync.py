
import os
import sys

# Usage: python odoo-bin shell -d odooMCD --root /opt/odoo < /mnt/custom_addons_project2/check_sync.py

print("--- DIAGNOSING CONTRACT SYNC ---")

Contract = env['trasas.contract']
ContractType = env['trasas.contract.type']
Document = env['documents.document']

root_ref = env.ref('trasas_contract_management.document_folder_contract_root', raise_if_not_found=False)
print(f"Root Folder Ref: {root_ref}")
if root_ref:
    print(f"Root Folder Name: {root_ref.name}, ID: {root_ref.id}, Type: {root_ref.type}, Active: {root_ref.active}")
    print(f"Root Parent (folder_id): {root_ref.folder_id.name if root_ref.folder_id else 'None'}")

print("\n--- CONTRACT TYPES ---")
for ct in ContractType.search([]):
    print(f"Type: {ct.name}, Code: {ct.code}, Folder: {ct.document_folder_id.name if ct.document_folder_id else 'MISSING'}")

print("\n--- LATEST CONTRACTS ---")
for c in Contract.search([], limit=10):
    print(f"Contract: {c.name}, Folder: {c.document_folder_id.name if c.document_folder_id else 'MISSING'}")
    attachments = env['ir.attachment'].search([('res_model', '=', 'trasas.contract'), ('res_id', '=', c.id)])
    print(f"  Attachments count: {len(attachments)}")
    for att in attachments:
        doc = Document.search([('attachment_id', '=', att.id)], limit=1)
        print(f"    - Attachment: {att.name}, Document: {doc.name if doc else 'NOT SYNCED'}, Folder: {doc.folder_id.name if doc and doc.folder_id else 'N/A'}")

print("--- END DIAGNOSIS ---")
