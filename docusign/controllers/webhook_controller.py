# -*- coding: utf-8 -*-
import logging
import json
import hmac
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

# Human-readable event labels for envelope-level webhook events
ENVELOPE_EVENT_MESSAGES = {
    'envelope-sent': _('Envelope sent to recipients'),
    'envelope-delivered': _('Envelope opened by recipients'),
    'envelope-completed': _('Envelope completed by all recipients'),
    'envelope-created': _('Envelope created'),
    'envelope-declined': _('Envelope declined by a recipient'),
    'envelope-voided': _('Envelope voided or expired'),
    'envelope-resent': _('Envelope resent'),
    'envelope-removed': _('Envelope permanently removed by DocuSign'),
    'envelope-corrected': _('Envelope corrected'),
    'envelope-purge': _('Envelope queued for purge'),
    'envelope-deleted': _('Envelope deleted after send'),
    'envelope-discard': _('Draft envelope discarded'),
    'envelope-reminder-sent': _('Reminder email sent'),
}

# Human-readable event labels for recipient-level webhook events
RECIPIENT_EVENT_MESSAGES = {
    'recipient-sent': _('Recipient notified to sign'),
    'recipient-autoresponded': _('Recipient email auto-responded or bounced'),
    'recipient-delivered': _('Recipient opened the envelope'),
    'recipient-completed': _('Recipient completed their actions'),
    'recipient-declined': _('Recipient declined to sign'),
    'recipient-authenticationfailed': _('Recipient failed authentication'),
    'recipient-resent': _('Envelope resent to recipient'),
    'recipient-delegate': _('Recipient delegation recorded'),
    'recipient-reassign': _('Recipient reassigned'),
    'recipient-finish-later': _('Recipient chose Finish Later'),
}


class DocuSignWebhookController(http.Controller):
    """
    Controller to handle DocuSign Connect webhook notifications.
    
    DocuSign Connect sends real-time notifications about envelope events:
    - sent: Envelope sent to recipient(s)
    - delivered: Envelope opened by recipient's email
    - completed: All recipients have signed
    - declined: A recipient declined to sign
    - voided: Envelope was voided/cancelled
    
    Security: Validates HMAC-SHA256 signature from DocuSign to ensure authenticity.
    
    Processing Flow:
    1. Verify HMAC signature for security
    2. Update local status based on webhook event
    3. Call status_docs() to verify status via API
    4. Auto-download signed document once on completion (deduped)
    5. Post audit messages to chatter
    
    This consolidates webhook handling from both odoo_docusign and contract_management
    into a single secure endpoint with proper verification and document retrieval.
    """

    @http.route('/docusign/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def docusign_webhook_handler(self, **kwargs):
        """
        Handle incoming DocuSign Connect webhook notifications.
        
        Expected payload structure (XML converted to JSON by DocuSign Connect):
        {
            "event": "envelope-completed",
            "apiVersion": "v2.1",
            "uri": "/restapi/v2.1/accounts/.../envelopes/...",
            "retryCount": 0,
            "configurationId": 12345,
            "generatedDateTime": "2026-01-10T12:00:00.0000000Z",
            "data": {
                "accountId": "...",
                "envelopeId": "...",
                "envelopeSummary": {
                    "status": "completed",
                    "emailSubject": "Please sign this document",
                    "recipients": {...},
                    "sender": {...}
                }
            }
        }
        """
        _logger.info("DocuSign webhook received")
        
        try:
            # Get raw request data and headers
            data = json.loads(request.httprequest.data.decode('utf-8'))
            headers = request.httprequest.headers
            
            # Verify HMAC signature for security
            if not self._verify_hmac_signature(request.httprequest.data, headers):
                _logger.warning("DocuSign webhook: HMAC signature verification failed")
                return {'status': 'error', 'message': 'Invalid signature'}
            
            # Extract envelope information
            envelope_data = data.get('data', {})
            envelope_id = envelope_data.get('envelopeId')
            envelope_status = envelope_data.get('envelopeSummary', {}).get('status')
            event_type = data.get('event', 'unknown')
            
            if not envelope_id:
                _logger.error("DocuSign webhook: Missing envelopeId in payload")
                return {'status': 'error', 'message': 'Missing envelope ID'}
            
            _logger.info("Processing webhook: event=%s, envelope=%s, status=%s", event_type, envelope_id, envelope_status)
            
            # Find the corresponding connector line
            ConnectorLine = request.env['docusign.connector.lines'].sudo()
            lines = ConnectorLine.search([('envelope_id', '=', envelope_id)])
            
            if not lines:
                _logger.warning("DocuSign webhook: No connector line found for envelope %s", envelope_id)
                return {'status': 'success', 'message': 'Envelope not tracked'}

            # Log every envelope/recipient event to the connector chatter (and subscription for recipient events)
            self._log_webhook_event(lines, event_type, envelope_status, envelope_data, data)
            
            # Mark recipient-level completion when event is recipient-completed
            self._mark_recipient_completion(lines, envelope_data, event_type)

            # Update status based on webhook event
            for line in lines:
                self._update_envelope_status(line, envelope_status, envelope_data, event_type)
                
                # Get parent connector record
                connector = line.record_id
                if connector:
                    # Refresh status from DocuSign API (verify webhook data)
                    try:
                        connector.status_docs()
                    except Exception as e:
                        _logger.warning("Failed to refresh status from API for envelope %s: %s", envelope_id, str(e))
                    
                    # Auto-download once when completed, skipping if already present
                    if envelope_status == 'completed':
                        self._download_signed_documents(lines, envelope_status=envelope_status, event_type=event_type, envelope_data=envelope_data)
            
            return {'status': 'success', 'message': 'Webhook processed'}
            
        except json.JSONDecodeError as e:
            _logger.exception("DocuSign webhook: Invalid JSON payload")
            return {'status': 'error', 'message': 'Invalid JSON'}
        except Exception as e:
            _logger.exception("DocuSign webhook: Unexpected error processing webhook")
            return {'status': 'error', 'message': 'Internal error'}

    def _verify_hmac_signature(self, raw_data, headers):
        IrConfigParameter = request.env['ir.config_parameter'].sudo()
        hmac_key_str = (IrConfigParameter.get_param('docusign.webhook_hmac_key', '') or '').strip()

        if not hmac_key_str:
            _logger.warning("DocuSign webhook HMAC key not configured - skipping signature verification")
            return True

        # Collect ALL signature headers DocuSign sent (signature-1, signature-2, ...)
        sig_headers = []
        for k, v in headers.items():
            if k.lower().startswith('x-docusign-signature-') and v:
                sig_headers.append(v.strip())

        if not sig_headers:
            _logger.warning("DocuSign webhook: Missing x-docusign-signature-* headers")
            return False

        # Use key exactly as stored (DocuSign HMAC key is a literal secret string)
        key_bytes = hmac_key_str.encode("utf-8")
        computed = base64.b64encode(hmac.new(key_bytes, raw_data, hashlib.sha256).digest()).decode("utf-8")

        _logger.info(
            "DocuSign webhook: computed_prefix=%s, headers_prefixes=%s",
            computed[:12],
            ", ".join(s[:12] for s in sig_headers),
        )

        # Match against ANY signature header value DocuSign provided
        for hdr in sig_headers:
            if hmac.compare_digest(computed, hdr):
                return True

        return False


    def _log_webhook_event(self, lines, event_type, envelope_status, envelope_data, payload):
        """Post a chatter message for every webhook event on the related connector(s).

        Recipient-level events are also mirrored to the subscription chatter when available.
        """
        if not lines:
            return

        message = self._build_event_message(event_type, envelope_status, envelope_data, payload)
        if not message:
            return

        connector_ids = set()
        for line in lines:
            connector = line.record_id
            if not connector or connector.id in connector_ids:
                continue

            try:
                connector.message_post(
                    body=message,
                    subject=_('DocuSign Webhook Event'),
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
            except Exception as e:
                _logger.warning("DocuSign webhook: Failed to post chatter message for connector %s: %s", connector.id, str(e))
            connector_ids.add(connector.id)

        if event_type and event_type.startswith('recipient-'):
            self._log_recipient_event_to_subscription(lines, message)


    def _log_recipient_event_to_subscription(self, lines, message):
        """Mirror recipient events into the subscription chatter when we can locate it."""
        subscription_ids = set()

        for line in lines:
            connector = line.record_id
            if not connector:
                continue

            subscription = connector.sale_id or getattr(connector.contract_management_id, 'subscription_id', False)
            if not subscription or subscription.id in subscription_ids:
                continue

            try:
                subscription.message_post(
                    body=message,
                    subject=_('DocuSign Recipient Event'),
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
            except Exception as e:
                _logger.warning("DocuSign webhook: Failed to post recipient event to subscription %s: %s", subscription.id, str(e))
            subscription_ids.add(subscription.id)


    def _build_event_message(self, event_type, envelope_status, envelope_data, payload):
        """Assemble a concise message for envelope or recipient webhook events."""
        if not event_type:
            return ''

        event_label = event_type
        if event_label.startswith('recipient-'):
            event_label = event_label[len('recipient-'):]
        elif event_label.startswith('envelope-'):
            event_label = event_label[len('envelope-'):]
        event_label = (event_label or '').replace('-', ' ').strip() or event_type
        event_label = event_label.capitalize()

        recipient_name = self._get_recipient_name(envelope_data)
        event_time = self._format_event_time(payload) or _('unknown time')

        return _('Contract %(event)s to %(recipient)s at %(time)s') % {
            'event': event_label,
            'recipient': recipient_name,
            'time': event_time,
        }


    def _get_recipient_name(self, envelope_data):
        if not isinstance(envelope_data, dict):
            return _('Recipient')

        recipient_id = envelope_data.get('recipientId') or envelope_data.get('recipient_id')
        signers = envelope_data.get('envelopeSummary', {}).get('recipients', {}).get('signers', []) or []

        if recipient_id:
            for signer in signers:
                if str(signer.get('recipientId')) == str(recipient_id):
                    name = signer.get('name') or signer.get('email')
                    if name:
                        return name

        for signer in signers:
            name = signer.get('name') or signer.get('email')
            if name:
                return name

        return _('Recipient')


    def _format_event_time(self, payload):
        if not isinstance(payload, dict):
            return None

        raw_time = payload.get('generatedDateTime') or payload.get('eventDateTime')
        if not raw_time:
            return None

        try:
            iso_value = raw_time.replace('Z', '+00:00')
            event_dt = datetime.fromisoformat(iso_value)
            if event_dt.tzinfo is None:
                event_dt = event_dt.replace(tzinfo=timezone.utc)

            local_tz = timezone(timedelta(hours=-6), name='UTC-6')
            local_dt = event_dt.astimezone(local_tz)
            return local_dt.strftime('%Y-%m-%d %H:%M %Z')
        except Exception:
            return raw_time


    def _mark_recipient_completion(self, lines, envelope_data, event_type):
        """
        For recipient-completed events, flag the corresponding connector lines as signed so
        the downstream status/state logic (status_docs) behaves the same as a manual status check.
        """
        if event_type != 'recipient-completed':
            return

        signers = envelope_data.get('envelopeSummary', {}).get('recipients', {}).get('signers', []) or []
        completed_ids = set()
        completed_emails = set()

        for signer in signers:
            if signer.get('status') == 'completed':
                if signer.get('recipientId'):
                    completed_ids.add(str(signer.get('recipientId')))
                email = (signer.get('email') or '').lower().strip()
                if email:
                    completed_emails.add(email)

        if not completed_ids and not completed_emails:
            return

        for line in lines:
            if line.sign_status:
                continue

            match_by_id = line.recipient_id and line.recipient_id in completed_ids
            match_by_email = line.email and line.email.lower().strip() in completed_emails

            if match_by_id or match_by_email:
                line.write({'sign_status': True, 'status': 'completed'})
                if line.record_id:
                    line.record_id.message_post(
                        body=_('Document signed by %s (webhook)') % line.partner_id.name,
                        subject=_('Signature Confirmed'),
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )

    def _update_envelope_status(self, line, status, envelope_data, event_type='unknown'):
        """
        Update connector line and parent record based on envelope status.
        
        Status mapping:
        - sent: Document sent to recipient
        - delivered: Document opened by recipient  
        - completed: Document signed by recipient
        - declined: Recipient declined to sign
        - voided: Envelope cancelled
        
        Args:
            line: docusign.connector.lines record
            status: Envelope status from webhook
            envelope_data: Full envelope data from webhook
            event_type: Type of webhook event (envelope-completed, recipient-completed, etc.)
        """
        _logger.info("Updating envelope %s: %s -> %s", line.envelope_id, line.status, status)
        
        status_map = {
            'sent': 'sent',
            'delivered': 'sent',  # Keep as 'sent' until completed
            'completed': 'completed',
            'declined': 'draft',  # Reset to draft if declined
            'voided': 'draft',  # Reset to draft if voided
        }
        
        new_status = status_map.get(status, line.status)
        
        # Update line status
        vals = {'status': new_status}
        
        if status == 'sent':
            vals['send_status'] = True
        elif status == 'completed':
            vals['sign_status'] = True
            vals['send_status'] = True
        elif status in ('declined', 'voided'):
            vals['sign_status'] = False
            vals['send_status'] = False
        
        line.write(vals)
        
        # Post message to chatter for audit trail
        message_map = {
            'sent': _('Document sent to %s') % line.partner_id.name,
            'delivered': _('Document delivered to %s') % line.partner_id.name,
            'completed': _('Document signed by %s') % line.partner_id.name,
            'declined': _('Document declined by %s') % line.partner_id.name,
            'voided': _('Document voided for %s') % line.partner_id.name,
        }
        
        message = message_map.get(status, _('Envelope status updated: %s') % status)
        
        if line.record_id:
            line.record_id.message_post(
                body=message,
                subject=_('DocuSign Status Update'),
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

    def _download_signed_documents(self, lines, envelope_status=None, event_type=None, envelope_data=None):
        """
        Download signed documents for the provided connector lines once per connector,
        skipping if signed attachments already exist to avoid duplicate copies.
        """
        processed_connectors = set()

        for line in lines:
            connector = line.record_id
            if not connector or connector.id in processed_connectors:
                continue

            # If any signed attachments already exist for this connector, skip to avoid duplicates
            if any(connector.connector_line_ids.mapped('signed_attachment_ids')):
                _logger.info("Connector %s already has signed attachments; skipping auto-download", connector.id)
                processed_connectors.add(connector.id)
                continue

            try:
                connector.download_docs()
            except Exception as e:
                _logger.warning("Auto-download failed for connector %s: %s", connector.id, str(e))

            processed_connectors.add(connector.id)
            
            status_value = envelope_status or (envelope_data.get('envelopeSummary', {}).get('status') if envelope_data else None)
            event_value = event_type or ''

            # Update parent connector state based on ENVELOPE status from DocuSign
            # The envelope_status reflects the overall envelope state, not individual recipient
            # CRITICAL: Only mark as completed when envelope itself is completed (all required signatures)
            # DocuSign may send 'recipient-completed' events, but envelope stays 'sent' until all sign
            if status_value == 'completed' and event_value in ('envelope-completed', 'envelope-complete'):
                # DocuSign reports ENVELOPE as completed - ALL required signatures collected
                # Only trust envelope-level completion events, not recipient-level
                line.record_id.write({'state': 'completed'})
                line.record_id.message_post(
                    body=_('All recipients have signed the document'),
                    subject=_('DocuSign Completion'),
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                _logger.info("Connector %s marked as completed - DocuSign envelope completed (event: %s)", 
                            line.record_id.id, event_value)
                
                # Extract custom fields from envelope and update contract.management record
                self._update_contract_custom_fields(line, envelope_data)
            elif status_value in ('sent', 'delivered'):
                # Envelope sent/delivered - move to appropriate intermediate state
                if line.record_id.state == 'new':
                    line.record_id.write({'state': 'sent'})
                    _logger.info("Connector %s moved to sent state", line.record_id.id)
                # Check if any recipients have signed (partial completion)
                elif any(l.sign_status for l in line.record_id.connector_line_ids):
                    if line.record_id.state not in ('customer', 'completed'):
                        line.record_id.write({'state': 'customer'})
                        _logger.info("Connector %s moved to customer state - partial signatures", line.record_id.id)
        
        _logger.info("Envelope %s updated successfully", line.envelope_id)
    
    def _update_contract_custom_fields(self, line, envelope_data):
        """
        Extract custom fields from DocuSign envelope and update related contract.management record.
        
        Args:
            line: docusign.connector.lines record
            envelope_data: Full envelope data from webhook containing customFields
        """
        try:
            # Find related contract.management record via docusign.connector
            connector = line.record_id
            if not connector:
                _logger.warning("No connector found for line %s", line.id)
                return
            
            ContractManagement = request.env['contract.management'].sudo()
            contract = ContractManagement.search([('docusign_id', '=', connector.id)], limit=1)
            
            if not contract:
                _logger.info("No contract.management record linked to connector %s", connector.id)
                return
            
            # Extract custom fields from envelope data
            envelope_summary = envelope_data.get('envelopeSummary', {}) if isinstance(envelope_data, dict) else {}
            custom_fields = envelope_summary.get('customFields', {})
            text_custom_fields = custom_fields.get('textCustomFields', [])
            
            if not text_custom_fields:
                _logger.info("No custom fields found in envelope for contract %s", contract.name)
                return
            
            # Parse custom fields and track changes
            updates = {}
            changes = []
            
            for field in text_custom_fields:
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                
                if field_name == 'monthly_payment' and field_value:
                    try:
                        new_value = float(field_value)
                        old_value = contract.monthly_payment or 0.0
                        updates['monthly_payment'] = new_value
                        _logger.info("Extracted monthly_payment: %s (original: %.2f)", field_value, old_value)
                        
                        # Check if value differs from original
                        if abs(new_value - old_value) > 0.01:  # Allow for small floating point differences
                            changes.append({
                                'field': 'Monthly Payment',
                                'old': old_value,
                                'new': new_value
                            })
                    except (ValueError, TypeError) as e:
                        _logger.warning("Failed to convert monthly_payment '%s' to float: %s", field_value, e)
                
                elif field_name == 'contract_value' and field_value:
                    try:
                        new_value = float(field_value)
                        old_value = contract.contract_value or 0.0
                        updates['contract_value'] = new_value
                        _logger.info("Extracted contract_value: %s (original: %.2f)", field_value, old_value)
                        
                        # Check if value differs from original
                        if abs(new_value - old_value) > 0.01:
                            changes.append({
                                'field': 'Contract Value',
                                'old': old_value,
                                'new': new_value
                            })
                    except (ValueError, TypeError) as e:
                        _logger.warning("Failed to convert contract_value '%s' to float: %s", field_value, e)
            
            if updates:
                contract.write(updates)
                _logger.info("Updated contract %s with custom fields: %s", contract.name, updates)
                
                # Post message to contract chatter
                if changes:
                    # Values changed - log the differences
                    change_lines = []
                    for change in changes:
                        change_lines.append(
                            f"• {change['field']}: ${change['old']:.2f} → ${change['new']:.2f}"
                        )
                    
                    contract.message_post(
                        body=_('Contract values updated from completed DocuSign envelope (values differ from original):<br/>%s') % '<br/>'.join(change_lines),
                        subject=_('DocuSign Custom Fields - Values Changed'),
                        message_type='comment',  # Use comment instead of notification for visibility
                        subtype_xmlid='mail.mt_comment'
                    )
                    _logger.warning("Contract %s custom field values differ from original: %s", contract.name, changes)
                else:
                    # Values match - simple confirmation
                    message_parts = []
                    if 'monthly_payment' in updates:
                        message_parts.append(f"Monthly Payment: ${updates['monthly_payment']:.2f}")
                    if 'contract_value' in updates:
                        message_parts.append(f"Contract Value: ${updates['contract_value']:.2f}")
                    
                    contract.message_post(
                        body=_('Contract values confirmed from DocuSign: %s') % ', '.join(message_parts),
                        subject=_('DocuSign Custom Fields'),
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )
            else:
                _logger.info("No valid custom fields to update for contract %s", contract.name)
                
        except Exception as e:
            _logger.exception("Error updating contract custom fields for line %s: %s", line.id, str(e))
            # Don't raise - this is not critical enough to fail the webhook

