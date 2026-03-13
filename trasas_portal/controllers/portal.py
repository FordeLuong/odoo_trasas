# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


from odoo.tools.image import image_data_uri


class CustomPortal(CustomerPortal):
    @http.route(["/my", "/my/home"], type="http", auth="user", website=True)
    def home(self, **kw):
        """Override home to add blog posts for news feed and manager approval data"""
        response = super(CustomPortal, self).home(**kw)

        # Check if current user is a line manager
        employee = request.env.user.employee_id
        is_manager = False
        approval_count = 0

        if employee:
            # Check if user has any subordinates
            subordinates = (
                request.env["hr.employee"]
                .sudo()
                .search([("parent_id", "=", employee.id)])
            )
            if subordinates:
                is_manager = True
                # Count pending approval requests from subordinates
                # 1. Count pending shift approvals (planning.slot)
                sub_resource_ids = subordinates.mapped("resource_id").ids
                PlanningSlot = request.env["planning.slot"].sudo()
                if "approval_state" in PlanningSlot._fields:
                    shift_count = PlanningSlot.search_count(
                        [
                            ("resource_id", "in", sub_resource_ids),
                            ("approval_state", "=", "to_approve"),
                        ]
                    )
                else:
                    shift_count = 0

                # 2. Count pending approval.request from subordinates
                # (where subordinate is request owner and current user is approver)
                ApprovalRequest = request.env["approval.request"].sudo()
                sub_user_ids = subordinates.mapped("user_id").ids
                approval_request_count = ApprovalRequest.search_count(
                    [
                        ("request_owner_id", "in", sub_user_ids),
                        ("request_status", "=", "pending"),
                    ]
                )

                approval_count = shift_count + approval_request_count

        # Add context variables to response
        if hasattr(response, "qcontext"):
            response.qcontext["image_data_uri"] = image_data_uri
            response.qcontext["user"] = request.env.user
            response.qcontext["is_manager"] = is_manager
            response.qcontext["approval_count"] = approval_count

        return response

    # =========================================================
    # APPROVALS MOVED TO M02_P0200_00
    # =========================================================
