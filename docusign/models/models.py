from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from . import docu_client
import base64
import re

_logger = logging.getLogger(__name__)

try:
    from docusign_esign import ApiClient
    api_client = ApiClient()
except Exception:
    _logger.warning('Package docusign-esign not found. Some features may be limited.')


class DocusignConnector(models.Model):
    _name = 'docusign.connector'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Docusign Records'

    user_account_id = fields.Many2one('res.users', string='DocuSign Account', default=lambda self: self.env.user, readonly=True)
    name = fields.Char(string='Sequence', copy=False, readonly=True, default='New')
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('docusign.connector') or 'New'
        return super(DocusignConnector, self).create(vals)

    responsible_id = fields.Many2one('res.users', string='Responsible', tracking=True)
    res_model = fields.Many2one('ir.model', string='Model')
    linked_record_id = fields.Integer(string='Linked Record')
    state = fields.Selection(
        [
            ('new', 'New'),
            ('open', 'Open'),
            ('sent', 'Sent'),
            ('customer', 'Customer Signed'),
            ('completed', 'Completed'),
        ],
        default='new',
        tracking=True,
        required=True
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'docusign_record_ir_attachments_rel',
        'docusign_record_id',
        'attachment_id',
        string='Attachments (Only PDF)'
    )
    connector_line_ids = fields.One2many(
        'docusign.connector.lines',
        'record_id',
        string='Connector Lines'
    )
    docs_policy = fields.Selection(
        [('in', 'In Hierarchy'), ('out', 'Simultaneously')],
        default='out',
        tracking=True,
        required=True
    )

    #invisible fields
    model = fields.Selection([('open', 'Open'),('contacts', 'Contacts'), ('sale', 'Sale'),
                              ('purchase', 'Purchase'),('invoice','Invoice')], default='open')
    sale_id = fields.Many2one('sale.order', string='Sale Order', ondelete='cascade')
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order', ondelete='cascade')
    invoice_id = fields.Many2one('account.move', string='Invoice', ondelete='cascade')
    contact_id = fields.Many2one('res.partner', string='Contact', ondelete='cascade')

    def send_docs(self):
        """Send documents to recipients via DocuSign."""
        _logger.info("[DocuSign API] send_docs() called for connector ID=%s, name=%s, policy=%s", 
                    self.id, self.name, self.docs_policy)
        try:
            user = self.env.user
            _logger.info("[DocuSign API] User: %s (ID=%s)", user.name, user.id)
            
            if not self.attachment_ids:
                _logger.error("[DocuSign API] Validation failed: No attachments for connector %s", self.id)
                raise ValidationError(_('Please attach at least one PDF document before sending.'))
            if not self.connector_line_ids:
                _logger.error("[DocuSign API] Validation failed: No recipients for connector %s", self.id)
                raise ValidationError(_("Please add at least one recipient before sending documents."))
            
            _logger.info("[DocuSign API] Attachments: %d, Recipients: %d", 
                        len(self.attachment_ids), len(self.connector_line_ids))

            if self.docs_policy == 'in':
                next_recipient = self.connector_line_ids.filtered(lambda r: not r.send_status)

                if not next_recipient:
                    raise ValidationError(_("Documents have already been sent to all recipients."))

                line = next_recipient[0]

                if not line.partner_id.email:
                    raise ValidationError(_('Email address is missing for recipient: %s. Please update the contact information.') % line.partner_id.name)

                previous_recipients = self.connector_line_ids.filtered(lambda r: r.id < line.id)
                incomplete_previous = previous_recipients.filtered(lambda r: not r.sign_status)

                if incomplete_previous:
                    raise ValidationError(
                        _("Cannot send to %s yet. Please wait for %s to complete their signature first.") % (
                            line.partner_id.name, incomplete_previous[0].partner_id.name))

                signed_attachment = previous_recipients.filtered(lambda r: r.sign_status).sorted(key=lambda r: r.id,
                                                                                                 reverse=True).mapped(
                    'signed_attachment_ids')
                if signed_attachment:
                    attach_file = signed_attachment[0]
                else:
                    attach_file = self.attachment_ids[0]

                attach_file_name = attach_file.name
                attach_file_data = attach_file.sudo().read(['datas'])
                file_data_encoded_string = attach_file_data[0]['datas']
                file_size = len(file_data_encoded_string) if file_data_encoded_string else 0
                _logger.info("[DocuSign API] File prepared: %s, size=%d bytes (base64)", attach_file_name, file_size)

                _logger.info("[DocuSign API] Sending envelope to %s (%s) for record %s", 
                            line.partner_id.name, line.partner_id.email, self.name)
                envelope_id = docu_client.send_docusign_file(
                    self.env, user, attach_file_name, file_data_encoded_string, line.partner_id.name, line.partner_id.email, line.partner_id
                )
                _logger.info("[DocuSign API] Envelope created successfully: envelope_id=%s", envelope_id)

                line.un_signed_attachment_ids |= attach_file
                line.sudo().write({
                    'status': 'sent',
                    'name': attach_file.name,
                    'envelope_id': envelope_id,
                    'send_status': True,
                })
                _logger.info("[DocuSign API] Connector line updated: ID=%s, envelope_id=%s, status=sent", 
                            line.id, envelope_id)

                self.write({'state': 'sent'})
                _logger.info("[DocuSign API] Connector state updated to 'sent' for ID=%s", self.id)
                self.message_post(
                    body=_('Document sent to %s for signature') % line.partner_id.name,
                    subject=_('Document Sent'),
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                self.env.cr.commit()
                return self.action_of_button(_("Document sent successfully to: %s") % line.partner_id.name)

            if self.docs_policy == 'out':
                for line in self.connector_line_ids:
                    if not line.partner_id.email:
                        raise ValidationError(_('Email address is missing for recipient: %s. Please update the contact information.') % line.partner_id.name)

                    for file in self.attachment_ids:
                        attach_file_name = file.name
                        filename, file_extension = os.path.splitext(attach_file_name)
                        if file_extension.lower() != '.pdf':
                            raise ValidationError(_('Only PDF files are supported. Please convert %s to PDF format.') % attach_file_name)
                        
                        attach_file_data = file.sudo().read(['datas'])
                        file_data_encoded_string = attach_file_data[0]['datas']
                        file_size = len(file_data_encoded_string) if file_data_encoded_string else 0
                        _logger.info("[DocuSign API] File prepared: %s, size=%d bytes (base64)", attach_file_name, file_size)

                        _logger.info("[DocuSign API] Sending envelope to %s (%s) for record %s", 
                                    line.partner_id.name, line.partner_id.email, self.name)
                        envelop_id = docu_client.send_docusign_file(
                            self.env, user, attach_file_name, file_data_encoded_string, line.partner_id.name, line.partner_id.email, line.partner_id)
                        _logger.info("[DocuSign API] Envelope created successfully: envelope_id=%s", envelop_id)

                        line.un_signed_attachment_ids |= file
                        line.sudo().write({
                            'status': 'sent',
                            'name': file.name,
                            'envelope_id': envelop_id,
                            'send_status': True
                        })
                        _logger.info("[DocuSign API] Connector line updated: ID=%s, envelope_id=%s, status=sent", 
                                    line.id, envelop_id)
                        
                        self.message_post(
                            body=_('Document %s sent to %s for signature') % (file.name, line.partner_id.name),
                            subject=_('Document Sent'),
                            message_type='notification',
                            subtype_xmlid='mail.mt_note'
                        )
                        
                self.write({'state': 'sent'})
                _logger.info("[DocuSign API] Connector state updated to 'sent' for ID=%s", self.id)
                _logger.info("[DocuSign API] SUCCESS: All documents sent successfully for connector %s", self.name)
                self.env.cr.commit()
                return self.action_of_button(_("Documents sent successfully to all recipients!"))

        except ValidationError:
            # Re-raise ValidationErrors as-is (already user-friendly)
            _logger.warning("[DocuSign API] Validation error in send_docs for connector %s", self.name)
            raise
        except Exception as e:
            _logger.exception("[DocuSign API] EXCEPTION in send_docs for connector %s", self.name)
            raise ValidationError(_("An unexpected error occurred while sending documents. Please contact support."))

    def download_docs(self):
        """Download signed documents from DocuSign and store in ir.attachment."""
        _logger.info("[DocuSign API] download_docs() called for connector ID=%s, name=%s", self.id, self.name)
        try:
            user = self.env.user
            if self.docs_policy == 'in':
                last_recipient = self.connector_line_ids.filtered(lambda r: r.send_status and not r.sign_status)
                if not last_recipient:
                    raise ValidationError(_('No recipients available for document download.'))

                line = last_recipient[0]
                if not line.envelope_id:
                    _logger.error("[DocuSign API] Missing envelope_id for line %s", line.id)
                    raise ValidationError(_('Document download failed: Missing DocuSign envelope ID.'))

                _logger.info("[DocuSign API] Downloading document for envelope %s (recipient: %s)", 
                            line.envelope_id, line.partner_id.name)
                docu_status, doc_data = docu_client.download_documents(self.env, user, line.envelope_id)
                _logger.info("[DocuSign API] Download result: status=%s, has_data=%s", 
                            docu_status, bool(doc_data))
                
                if docu_status == 'completed' and doc_data:
                    attachment = self.env['ir.attachment'].sudo().create({
                        'name': doc_data['filename'],
                        'type': 'binary',
                        'datas': base64.b64encode(doc_data['content']),
                        'mimetype': doc_data['mimetype'],
                        'res_model': 'docusign.connector.lines',
                        'res_id': line.id,
                        'description': f"Signed document from DocuSign envelope {line.envelope_id}"
                    })
                    _logger.info("[DocuSign API] Attachment created: ID=%s, name=%s, size=%d bytes", 
                                attachment.id, doc_data['filename'], len(doc_data['content']))

                    line.sudo().write({
                        'signed_attachment_ids': [(4, attachment.id)],
                        'status': 'completed',
                        'sign_status': True,
                    })
                    _logger.info("[DocuSign API] Line marked as completed: ID=%s", line.id)
                    
                    # Log to chatter
                    self.message_post(
                        body=_('Document signed by %s and downloaded successfully') % line.partner_id.name,
                        subject=_('Document Completed'),
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )
                    
                    # Pass signed doc to next recipient
                    next_recipient = self.connector_line_ids.filtered(lambda r: r.id > line.id and not r.send_status)
                    if next_recipient:
                        next_recipient[0].un_signed_attachment_ids |= attachment

            if self.docs_policy == 'out':
                for line in self.connector_line_ids:
                    if not line.envelope_id:
                        raise ValidationError(_('Document download failed: Missing DocuSign envelope ID for %s.') % line.partner_id.name)
                    if line.send_status and not line.sign_status:
                        _logger.info("Downloading document for envelope %s (recipient: %s)", line.envelope_id, line.partner_id.name)
                        docu_status, doc_data = docu_client.download_documents(self.env, user, line.envelope_id)
                        
                        if docu_status == 'completed' and doc_data:
                            attachment = self.env['ir.attachment'].sudo().create({
                                'name': doc_data['filename'],
                                'type': 'binary',
                                'datas': base64.b64encode(doc_data['content']),
                                'mimetype': doc_data['mimetype'],
                                'res_model': 'docusign.connector.lines',
                                'res_id': line.id,
                                'description': f"Signed document from DocuSign envelope {line.envelope_id}"
                            })
                            line.sudo().write({
                                'signed_attachment_ids': [(4, attachment.id)],
                                'status': 'completed',
                                'sign_status': True,
                            })
                            
                            # Log to chatter
                            self.message_post(
                                body=_('Document signed by %s and downloaded successfully') % line.partner_id.name,
                                subject=_('Document Completed'),
                                message_type='notification',
                                subtype_xmlid='mail.mt_note'
                            )

            # Note: Connector completion state is managed by webhook handler
            # Do not automatically mark as completed here - let webhook handle state transitions
            _logger.info("[DocuSign API] download_docs() completed for connector %s", self.id)
                
            return self.action_of_button(_('Documents downloaded and stored successfully'))
            
        except ValidationError:
            # Re-raise ValidationErrors as-is (already user-friendly)
            raise
        except Exception as e:
            _logger.exception("Error downloading documents for DocuSign record %s", self.name)
            raise ValidationError(_("An unexpected error occurred while downloading documents. Please contact support."))


    def status_docs(self):
        """Check signature status for all envelopes."""
        _logger.info("[DocuSign API] status_docs() called for connector ID=%s, name=%s", self.id, self.name)
        try:
            user = self.env.user
            for line in self.connector_line_ids:
                if not line.envelope_id:
                    raise ValidationError(_('Cannot check status: DocuSign envelope ID is missing for %s.') % line.partner_id.name)
                if not line.sign_status:
                    _logger.info("[DocuSign API] Checking status for envelope %s (recipient: %s)", 
                                line.envelope_id, line.partner_id.name)
                    docu_status = docu_client.get_status(self.env, user, line.envelope_id)
                    _logger.info("[DocuSign API] Status check result: envelope=%s, status=%s", 
                                line.envelope_id, docu_status)
                    if docu_status == 'completed':
                        line.sudo().write({
                            'status': 'completed',
                            'sign_status': True,
                        })
                        self.message_post(
                            body=_('Document signed by %s (verified via status check)') % line.partner_id.name,
                            subject=_('Signature Confirmed'),
                            message_type='notification',
                            subtype_xmlid='mail.mt_note'
                        )
            
            # Update connector state based on customer signature progress. Legacy extra signers
            # should not block completion; prefer the customer partner linked to sale_id.
            relevant_lines = self.connector_line_ids
            if self.sale_id and self.sale_id.partner_id:
                customer_lines = relevant_lines.filtered(lambda l: l.partner_id == self.sale_id.partner_id)
                if customer_lines:
                    relevant_lines = customer_lines

            signed_lines = [l for l in relevant_lines if l.sign_status]
            total_lines = len(relevant_lines)
            _logger.info(
                "[DocuSign API] Connector %s - Signed %s/%s customer lines", self.id, len(signed_lines), total_lines
            )

            all_signed = all(l.sign_status for l in relevant_lines) if relevant_lines else False
            any_signed = any(l.sign_status for l in relevant_lines) if relevant_lines else False

            _logger.info(
                "[DocuSign API] Connector %s state before update=%s, any_signed=%s, all_signed=%s",
                self.id,
                self.state,
                any_signed,
                all_signed,
            )

            if all_signed:
                self.write({'state': 'completed'})
            elif any_signed:
                self.write({'state': 'customer'})

            _logger.info("[DocuSign API] status_docs() completed for connector %s", self.id)
            
            return self.action_of_button(_('Status check completed successfully'))
            
        except ValidationError:
            # Re-raise ValidationErrors as-is (already user-friendly)
            raise
        except Exception as e:
            _logger.exception("Error checking status for DocuSign record %s", self.name)
            raise ValidationError(_("An unexpected error occurred while checking signature status. Please try again or contact support."))

    def action_of_button(self, message):
        message_id = self.env['message.wizard'].create({'message': _(message)})
        return {
            'name': _('Successful'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }


class DocusignConnectorLines(models.Model):
    _name = 'docusign.connector.lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Docusign Connector Lines'
    _sql_constraints = [
        # Multi-signer envelopes: one line per signer (partner) per envelope
        # Composite unique: (envelope_id, partner_id) - allows NULL envelope_id for unsent lines
        ('envelope_id_partner_unique', 'UNIQUE(envelope_id, partner_id)', 'Each partner can appear only once per envelope!'),
        ('partner_required', 'CHECK(partner_id IS NOT NULL)', 'Recipient partner is required!')
    ]

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        tracking=True,
        required=True,
        ondelete='restrict'
    )
    email = fields.Char(string='Email', related='partner_id.email', store=True)
    status = fields.Selection(
        [('draft', 'Draft'), ('sent', 'Sent'), ('completed', 'Completed')],
        default='draft',
        readonly=True,
        tracking=True,
        required=True
    )

    un_signed_attachment_ids = fields.Many2many(
        'ir.attachment',
        'lines_unsigned_ir_attachments_rel',
        'attachment_id',
        'docusign_record_id',
        string='Unsigned Attachments'
    )
    signed_attachment_ids = fields.Many2many(
        'ir.attachment',
        'lines_signed_ir_attachments_rel',
        'attachment_id',
        'docusign_record_id',
        string='Signed Attachments'
    )

    name = fields.Char(string="Document Name", tracking=True)
    envelope_id = fields.Char(string="Envelope ID", readonly=True, tracking=True, index=True)

    send_status = fields.Boolean(string="Send Status", readonly=True, tracking=True, default=False)
    sign_status = fields.Boolean(string="Sign Status", readonly=True, tracking=True, default=False)
    docs_policy = fields.Selection(related='record_id.docs_policy', store=True)
    recipient_id = fields.Char(string='DocuSign Recipient ID')
    client_user_id = fields.Char(string='Embedded Client User ID', help='DocuSign clientUserId to enable embedded signing')
    embedded_signing_url = fields.Char(string='Embedded Signing URL', readonly=True)
    embedded_started_at = fields.Datetime(string='Embedded Signing Started At', readonly=True)
    embedded_completed_at = fields.Datetime(string='Embedded Signing Completed At', readonly=True)
    embedded_event = fields.Char(string='Last Embedded Event', readonly=True)

    record_id = fields.Many2one(
        'docusign.connector',
        string='Record',
        ondelete='cascade',
        required=True
    )

    @api.constrains('partner_id')
    def _check_partner_email(self):
        """Validate that partner has a valid email address."""
        for line in self:
            candidate = getattr(line, 'recipient_email', None) or line.partner_id.email
            if line.partner_id and not candidate:
                raise ValidationError(
                    _('Recipient %s must have an email address before sending documents.') % line.partner_id.name
                )
            if line.partner_id and candidate:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, candidate):
                    raise ValidationError(
                        _('Invalid email address for recipient %s: %s') % (line.partner_id.name, candidate)
                    )

    @api.constrains('envelope_id', 'status')
    def _check_envelope_consistency(self):
        """Ensure envelope_id is set when status is sent or completed."""
        for line in self:
            if line.status in ('sent', 'completed') and not line.envelope_id:
                raise ValidationError(
                    _('Cannot mark document as %s without a DocuSign Envelope ID.') % line.status
                )