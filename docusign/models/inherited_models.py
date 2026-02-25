from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError
import base64

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    docusign_connector_ids = fields.One2many('docusign.connector', 'contact_id', string="DocuSign Documents")

    def action_get_signature(self):
        # Create a Docusign Connector record
        docusign_connector = self.env['docusign.connector'].create({
            'name': self.env['ir.sequence'].next_by_code('docusign.connector') or 'New',
            'model': 'contacts',
            'res_model': self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1).id,
            'linked_record_id': self.id,
            'contact_id': self.id,
            'state': 'open',
            'responsible_id': self.user_id.id,
        })

        # Return an action to view the created connector in form view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Docusign Connector',
            'res_model': 'docusign.connector',
            'view_mode': 'form',
            'res_id': docusign_connector.id,  # ID of the newly created record
            'target': 'current',
        }

from datetime import timedelta
class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    docusign_connector_ids = fields.One2many('docusign.connector', 'sale_id', string="DocuSign Documents")

    def action_get_signature(self):
        # Create a Docusign Connector record
        docusign_connector = self.env['docusign.connector'].create({
            'name': self.env['ir.sequence'].next_by_code('docusign.connector') or 'New',
            'model': 'sale',
            'res_model': self.env['ir.model'].search([('model', '=', 'sale.order')], limit=1).id,
            'linked_record_id': self.id,
            'sale_id': self.id,
            'state': 'open',
            'responsible_id': self.user_id.id,
        })
        # Generate the Sale Order PDF (Quotation PDF)
        pdf_report = self.env.ref('sale.action_report_saleorder')._render_qweb_pdf([self.id])[0]

        # Encode the PDF as base64
        pdf_base64 = base64.b64encode(pdf_report)

        # Create an attachment for the generated PDF
        attachment = self.env['ir.attachment'].create({
            'name': f'Quotation_{self.name}.pdf',
            'type': 'binary',
            'datas': pdf_base64,
            'res_model': 'docusign.connector',  # Attach to docusign.connector
            'res_id': docusign_connector.id,  # Attach to the specific DocusignConnector record
            'mimetype': 'application/pdf',
        })

        # Add the attachment to the Many2many field 'attachment_ids'
        docusign_connector.attachment_ids = [(4, attachment.id)]
        # Return an action to view the created connector in form view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Docusign Connector',
            'res_model': 'docusign.connector',
            'view_mode': 'form',
            'res_id': docusign_connector.id,  # ID of the newly created record
            'target': 'current',
        }


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    docusign_connector_ids = fields.One2many('docusign.connector', 'purchase_id', string="DocuSign Documents")

    def action_get_signature(self):
        # Create a Docusign Connector record
        docusign_connector = self.env['docusign.connector'].create({
            'name': self.env['ir.sequence'].next_by_code('docusign.connector') or 'New',
            'model': 'purchase',
            'res_model': self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1).id,
            'linked_record_id': self.id,
            'purchase_id': self.id,
            'state': 'open',
            'responsible_id': self.user_id.id,
        })
        # Generate the Purchase Order PDF
        pdf_report = self.env.ref('purchase.action_report_purchase_order')._render_qweb_pdf([self.id])[0]

        # Encode the PDF as base64
        pdf_base64 = base64.b64encode(pdf_report)

        # Create an attachment for the generated PDF
        attachment = self.env['ir.attachment'].create({
            'name': f'Purchase_Order_{self.name}.pdf',
            'type': 'binary',
            'datas': pdf_base64,
            'res_model': 'docusign.connector',  # Attach to docusign.connector
            'res_id': docusign_connector.id,    # Attach to the specific DocusignConnector record
            'mimetype': 'application/pdf',
        })

        # Add the attachment to the Many2many field 'attachment_ids'
        docusign_connector.attachment_ids = [(4, attachment.id)]
        # Return an action to view the created connector in form view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Docusign Connector',
            'res_model': 'docusign.connector',
            'view_mode': 'form',
            'res_id': docusign_connector.id,  # ID of the newly created record
            'target': 'current',
        }


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    docusign_connector_ids = fields.One2many('docusign.connector', 'purchase_id', string="DocuSign Documents")

    def action_get_signature(self):
        # Create a Docusign Connector record
        docusign_connector = self.env['docusign.connector'].create({
            'name': self.env['ir.sequence'].next_by_code('docusign.connector') or 'New',
            'model': 'invoice',
            'res_model': self.env['ir.model'].search([('model', '=', 'account.move')], limit=1).id,
            'linked_record_id': self.id,
            'invoice_id': self.id,
            'state': 'open',
            'responsible_id': self.user_id.id,
        })
        # Generate the Purchase Order PDF
        pdf_report = self.env.ref('account.account_invoices')._render_qweb_pdf([self.id])[0]

        # Encode the PDF as base64
        pdf_base64 = base64.b64encode(pdf_report)

        # Create an attachment for the generated PDF
        attachment = self.env['ir.attachment'].create({
            'name': f'Invoice_{self.name}.pdf',
            'type': 'binary',
            'datas': pdf_base64,
            'res_model': 'docusign.connector',  # Attach to docusign.connector
            'res_id': docusign_connector.id,    # Attach to the specific DocusignConnector record
            'mimetype': 'application/pdf',
        })

        # Add the attachment to the Many2many field 'attachment_ids'
        docusign_connector.attachment_ids = [(4, attachment.id)]
        # Return an action to view the created connector in form view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Docusign Connector',
            'res_model': 'docusign.connector',
            'view_mode': 'form',
            'res_id': docusign_connector.id,  # ID of the newly created record
            'target': 'current',
        }