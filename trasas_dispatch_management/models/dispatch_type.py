from odoo import models, fields, api


class TrasasDispatchType(models.Model):
    _name = "trasas.dispatch.type"
    _description = "Loại công văn"
    _order = "name"

    name = fields.Char(string="Tên loại", required=True)
    code = fields.Char(string="Mã", help="Mã viết tắt (nếu có)")
    dispatch_type = fields.Selection(
        [("incoming", "Công văn đến"), ("outgoing", "Công văn đi")],
        string="Phân loại",
        required=True,
        default="incoming",
    )
    active = fields.Boolean(default=True)
    description = fields.Text(string="Mô tả")

    document_folder_id = fields.Many2one(
        "documents.document",
        string="Thư mục tài liệu (Documents)",
        domain="[('type', '=', 'folder')]",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._create_document_folder()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "name" in vals:
            for rec in self:
                if rec.document_folder_id:
                    rec.document_folder_id.sudo().write({"name": rec.name})
        return res

    def _create_document_folder(self):
        """Tự động tạo Folder cho Loại văn bản trong Documents app"""
        Document = self.env["documents.document"].sudo()
        
        for rec in self:
            if rec.document_folder_id:
                continue

            xml_id = "trasas_dispatch_management.document_workspace_dispatch"
            if rec.dispatch_type == "outgoing":
                xml_id = "trasas_dispatch_management.document_workspace_dispatch_outgoing"
            
            root_folder = self.env.ref(xml_id, raise_if_not_found=False)
            if not root_folder:
                continue

            folder = Document.create(
                {
                    "name": rec.name,
                    "type": "folder",
                    "folder_id": root_folder.id,
                }
            )
            rec.write({"document_folder_id": folder.id})

    @api.model
    def _create_folders_for_existing(self):
        """Tạo folder cho các loại công văn cũ khi Upgrade module"""
        records = self.search([("document_folder_id", "=", False)])
        records._create_document_folder()
