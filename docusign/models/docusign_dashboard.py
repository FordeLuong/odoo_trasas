# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class DocusignDashboard(models.Model):
    _name = 'docusign.dashboard'
    _description = 'DocuSign Dashboard Statistics'
    _order = 'create_date desc'

    name = fields.Char(string='Dashboard Name', default='DocuSign Overview', required=True)
    date_from = fields.Date(string='From Date', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='To Date', default=fields.Date.today)
    responsible_id = fields.Many2one('res.users', string='Filter by Responsible')
    
    # Summary Statistics
    total_records = fields.Integer(string='Total Records', compute='_compute_statistics', store=False)
    total_new = fields.Integer(string='New', compute='_compute_statistics', store=False)
    total_open = fields.Integer(string='Open', compute='_compute_statistics', store=False)
    total_sent = fields.Integer(string='Sent', compute='_compute_statistics', store=False)
    total_completed = fields.Integer(string='Completed', compute='_compute_statistics', store=False)
    
    # Recipient Statistics
    total_recipients = fields.Integer(string='Total Recipients', compute='_compute_statistics', store=False)
    recipients_pending = fields.Integer(string='Pending Signatures', compute='_compute_statistics', store=False)
    recipients_completed = fields.Integer(string='Signed', compute='_compute_statistics', store=False)
    
    # Performance Metrics
    avg_completion_time = fields.Float(string='Avg Completion Time (days)', compute='_compute_statistics', store=False)
    completion_rate = fields.Float(string='Completion Rate (%)', compute='_compute_statistics', store=False)
    
    # Recent Activity
    recent_sent = fields.Integer(string='Sent Last 7 Days', compute='_compute_statistics', store=False)
    recent_completed = fields.Integer(string='Completed Last 7 Days', compute='_compute_statistics', store=False)

    @api.depends('date_from', 'date_to', 'responsible_id')
    def _compute_statistics(self):
        """Compute all dashboard statistics based on filters."""
        for record in self:
            domain = []
            
            # Apply date filter
            if record.date_from:
                domain.append(('create_date', '>=', record.date_from))
            if record.date_to:
                domain.append(('create_date', '<=', record.date_to))
            
            # Apply responsible filter
            if record.responsible_id:
                domain.append(('responsible_id', '=', record.responsible_id.id))
            
            # Get connector records
            connectors = self.env['docusign.connector'].search(domain)
            
            # Basic statistics
            record.total_records = len(connectors)
            record.total_new = len(connectors.filtered(lambda r: r.state == 'new'))
            record.total_open = len(connectors.filtered(lambda r: r.state == 'open'))
            record.total_sent = len(connectors.filtered(lambda r: r.state == 'sent'))
            record.total_completed = len(connectors.filtered(lambda r: r.state == 'completed'))
            
            # Recipient statistics
            all_lines = connectors.mapped('connector_line_ids')
            record.total_recipients = len(all_lines)
            record.recipients_pending = len(all_lines.filtered(lambda l: l.send_status and not l.sign_status))
            record.recipients_completed = len(all_lines.filtered(lambda l: l.sign_status))
            
            # Completion rate
            if record.total_records > 0:
                record.completion_rate = (record.total_completed / record.total_records) * 100
            else:
                record.completion_rate = 0.0
            
            # Average completion time
            completed_records = connectors.filtered(lambda r: r.state == 'completed')
            if completed_records:
                total_days = 0
                count = 0
                for rec in completed_records:
                    # Find the last completed line to get completion date
                    last_completed_line = rec.connector_line_ids.filtered(lambda l: l.sign_status).sorted(key=lambda l: l.write_date, reverse=True)
                    if last_completed_line:
                        create_date = rec.create_date
                        complete_date = last_completed_line[0].write_date
                        if create_date and complete_date:
                            days_diff = (complete_date - create_date).total_seconds() / 86400
                            total_days += days_diff
                            count += 1
                record.avg_completion_time = total_days / count if count > 0 else 0.0
            else:
                record.avg_completion_time = 0.0
            
            # Recent activity (last 7 days)
            seven_days_ago = fields.Datetime.now() - timedelta(days=7)
            recent_domain = domain + [('create_date', '>=', seven_days_ago)]
            recent_connectors = self.env['docusign.connector'].search(recent_domain)
            record.recent_sent = len(recent_connectors.filtered(lambda r: r.state in ('sent', 'completed')))
            record.recent_completed = len(recent_connectors.filtered(lambda r: r.state == 'completed'))

    def action_view_new_records(self):
        """Open tree view of new records."""
        domain = [('state', '=', 'new')]
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        if self.responsible_id:
            domain.append(('responsible_id', '=', self.responsible_id.id))
        
        return {
            'name': 'New DocuSign Records',
            'type': 'ir.actions.act_window',
            'res_model': 'docusign.connector',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'create': False}
        }

    def action_view_sent_records(self):
        """Open tree view of sent records."""
        domain = [('state', '=', 'sent')]
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        if self.responsible_id:
            domain.append(('responsible_id', '=', self.responsible_id.id))
        
        return {
            'name': 'Sent DocuSign Records',
            'type': 'ir.actions.act_window',
            'res_model': 'docusign.connector',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'create': False}
        }

    def action_view_completed_records(self):
        """Open tree view of completed records."""
        domain = [('state', '=', 'completed')]
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        if self.responsible_id:
            domain.append(('responsible_id', '=', self.responsible_id.id))
        
        return {
            'name': 'Completed DocuSign Records',
            'type': 'ir.actions.act_window',
            'res_model': 'docusign.connector',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'create': False}
        }

    def action_view_pending_signatures(self):
        """Open tree view of connector lines with pending signatures."""
        domain = [('send_status', '=', True), ('sign_status', '=', False)]
        
        # Get connectors matching date/responsible filters
        connector_domain = []
        if self.date_from:
            connector_domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            connector_domain.append(('create_date', '<=', self.date_to))
        if self.responsible_id:
            connector_domain.append(('responsible_id', '=', self.responsible_id.id))
        
        if connector_domain:
            connectors = self.env['docusign.connector'].search(connector_domain)
            domain.append(('record_id', 'in', connectors.ids))
        
        return {
            'name': 'Pending Signatures',
            'type': 'ir.actions.act_window',
            'res_model': 'docusign.connector.lines',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'create': False}
        }

    def action_refresh_statistics(self):
        """Manual refresh button to recompute statistics."""
        self._compute_statistics()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Statistics Refreshed',
                'message': 'Dashboard statistics updated successfully',
                'type': 'success',
                'sticky': False,
            }
        }
