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
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)

    def _create_document_folder(self):
        """Không còn tạo Folder cho Loại văn bản trong Documents app (theo yêu cầu mới)"""
        pass

    @api.model
    def _create_folders_for_existing(self):
        """Không còn tạo folder cho các loại công văn cũ khi Upgrade module"""
        pass
