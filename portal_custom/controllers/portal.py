# -*- coding: utf-8 -*-
import json
from odoo import http, fields
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


from odoo.tools.image import image_data_uri


def get_cover_image_url(post):
    """Extract cover image URL from blog post's cover_properties JSON"""
    if not post.cover_properties:
        return None
    try:
        props = json.loads(post.cover_properties)
        bg_image = props.get('background-image', '')
        # Extract URL from "url('/path/to/image')" format
        if bg_image.startswith("url("):
            url = bg_image[4:-1].strip("'").strip('"')
            return url
    except (json.JSONDecodeError, ValueError):
        pass
    return None


class CustomPortal(CustomerPortal):

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        """ Override home to add blog posts for news feed and manager approval data """
        response = super(CustomPortal, self).home(**kw)
        
        # Fetch published blog posts for news feed
        BlogPost = request.env['blog.post'].sudo()
        blog_posts = BlogPost.search([
            ('is_published', '=', True),
        ], order='post_date desc', limit=20)
        
        # Fetch upcoming events
        PortalEvent = request.env['portal.event'].sudo()
        upcoming_events = PortalEvent.search([
            ('date', '>=', fields.Date.today()),
        ], order='date asc', limit=5)
        
        # Check if current user is a line manager
        employee = request.env.user.employee_id
        is_manager = False
        approval_count = 0
        
        if employee:
            # Check if user has any subordinates
            subordinates = request.env['hr.employee'].sudo().search([
                ('parent_id', '=', employee.id)
            ])
            if subordinates:
                is_manager = True
                # Count pending approval requests from subordinates
                # 1. Count pending shift approvals (planning.slot)
                sub_resource_ids = subordinates.mapped('resource_id').ids
                PlanningSlot = request.env['planning.slot'].sudo()
                if 'approval_state' in PlanningSlot._fields:
                    shift_count = PlanningSlot.search_count([
                        ('resource_id', 'in', sub_resource_ids),
                        ('approval_state', '=', 'to_approve'),
                    ])
                else:
                    shift_count = 0
                
                # 2. Count pending approval.request from subordinates
                # (where subordinate is request owner and current user is approver)
                ApprovalRequest = request.env['approval.request'].sudo()
                sub_user_ids = subordinates.mapped('user_id').ids
                approval_request_count = ApprovalRequest.search_count([
                    ('request_owner_id', 'in', sub_user_ids),
                    ('request_status', '=', 'pending'),
                ])
                
                approval_count = shift_count + approval_request_count
        

        # Check permissions for posting news (HR Officers or Managers or Admin)
        can_post_news = request.env.user.has_group('hr.group_hr_user') or request.env.user.has_group('base.group_system')

        # Add blog posts and context variables to response
        if hasattr(response, 'qcontext'):
            response.qcontext['blog_posts'] = blog_posts
            response.qcontext['upcoming_events'] = upcoming_events
            response.qcontext['slug'] = request.env['ir.http']._slug
            response.qcontext['image_data_uri'] = image_data_uri
            response.qcontext['user'] = request.env.user
            response.qcontext['get_cover_image_url'] = get_cover_image_url
            response.qcontext['is_manager'] = is_manager
            response.qcontext['approval_count'] = approval_count
            response.qcontext['can_post_news'] = can_post_news
        
        return response

    @http.route(['/my/news/post'], type='http', auth='user', methods=['POST'], website=True)
    def post_news(self, **kw):
        """ Handle news posting from portal (HR or Admin only) """
        if not (request.env.user.has_group('hr.group_hr_user') or request.env.user.has_group('base.group_system')):
            return request.redirect('/my')

        content = kw.get('content')
        if not content:
            return request.redirect('/my')

        # Find a default blog (e.g., 'News' or first available)
        Blog = request.env['blog.blog'].sudo()
        blog = Blog.search([('name', 'ilike', 'News')], limit=1)
        if not blog:
            blog = Blog.search([], limit=1)
        
        if not blog:
            return request.redirect('/my?error=no_blog_found')

        # Create the post
        BlogPost = request.env['blog.post'].sudo()
        
        # Use first few words as title
        title = content[:50] + '...' if len(content) > 50 else content
        
        post = BlogPost.create({
            'blog_id': blog.id,
            'name': title,
            'subtitle': content, # Using subtitle as main content for simple posts
            'author_id': request.env.user.partner_id.id,
            'is_published': True, # Publish immediately
        })
        
        return request.redirect('/my?success=post_created')

    @http.route(['/my/news/post/delete/<int:post_id>'], type='http', auth='user', website=True)
    def delete_news(self, post_id, **kw):
        """ Handle post deletion """
        BlogPost = request.env['blog.post'].sudo()
        post = BlogPost.browse(post_id)
        
        if not post.exists():
            return request.redirect('/my?error=post_not_found')
            
        # Check permissions: HR or Admin only
        is_hr_or_admin = request.env.user.has_group('hr.group_hr_user') or request.env.user.has_group('base.group_system')
        
        if is_hr_or_admin:
            post.unlink()
            return request.redirect('/my?success=post_deleted')
            
        return request.redirect('/my?error=access_denied')

    # =====================
    # PORTAL APPS
    # =====================

    @http.route(['/my/leaves'], type='http', auth='user', website=True)
    def portal_leaves(self, **kw):
        return request.render('portal_custom.portal_app_leaves', {
            'user': request.env.user,
            'app_name': 'Leaves',
        })

    @http.route(['/my/personal-information'], type='http', auth='user', website=True)
    def portal_personal_information(self, **kw):
        return request.render('portal_custom.portal_app_personal_information', {
            'user': request.env.user,
            'app_name': 'Personal Information',
        })

    @http.route(['/my/rocks'], type='http', auth='user', website=True)
    def portal_rocks(self, **kw):
        return request.render('portal_custom.portal_app_rocks', {
            'user': request.env.user,
            'app_name': 'Rocks',
        })

    @http.route(['/my/performance'], type='http', auth='user', website=True)
    def portal_performance(self, **kw):
        return request.render('portal_custom.portal_app_performance', {
            'user': request.env.user,
            'app_name': 'Performance',
        })

    @http.route(['/my/team-accountabilities'], type='http', auth='user', website=True)
    def portal_team_accountabilities(self, **kw):
        return request.render('portal_custom.portal_app_team_accountabilities', {
            'user': request.env.user,
            'app_name': 'Team Accountabilities',
        })

    @http.route(['/my/appraisals'], type='http', auth='user', website=True)
    def portal_appraisals(self, **kw):
        return request.render('portal_custom.portal_app_appraisals', {
            'user': request.env.user,
            'app_name': 'Appraisals',
        })

    @http.route(['/my/employee-engagement'], type='http', auth='user', website=True)
    def portal_employee_engagement(self, **kw):
        return request.render('portal_custom.portal_app_employee_engagement', {
            'user': request.env.user,
            'app_name': 'Employee Engagement',
        })

    @http.route(['/my/expenses'], type='http', auth='user', website=True)
    def portal_expenses(self, **kw):
        return request.render('portal_custom.portal_app_expenses', {
            'user': request.env.user,
            'app_name': 'Expenses',
        })

    @http.route(['/my/cond'], type='http', auth='user', website=True)
    def portal_cond(self, **kw):
        return request.render('portal_custom.portal_app_cond', {
            'user': request.env.user,
            'app_name': 'COND',
        })

    @http.route(['/my/payslips'], type='http', auth='user', website=True)
    def portal_payslips(self, **kw):
        return request.render('portal_custom.portal_app_payslips', {
            'user': request.env.user,
            'app_name': 'Payslips',
        })

    @http.route(['/my/knowledge-hub'], type='http', auth='user', website=True)
    def portal_knowledge_hub(self, **kw):
        return request.render('portal_custom.portal_app_knowledge_hub', {
            'user': request.env.user,
            'app_name': 'Knowledge Hub',
        })

    @http.route(['/my/settings'], type='http', auth='user', website=True)
    def portal_settings(self, **kw):
        values = self._prepare_portal_layout_values()
        values.update({
            'user': request.env.user,
        })
        return request.render('portal_custom.portal_settings_page', values)

    # =========================================================
    # APPROVALS MOVED TO M02_P0200_00
    # =========================================================

