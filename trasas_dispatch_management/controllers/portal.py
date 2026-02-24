# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class DispatchPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        """Add dispatch count to portal homepage"""
        values = super()._prepare_home_portal_values(counters)
        if "dispatch_count" in counters:
            # Count dispatches assigned to current user
            dispatch_count = request.env["trasas.dispatch.incoming"].search_count(
                [
                    ("handler_ids", "in", [request.env.user.id]),
                    ("state", "in", ["processing", "waiting_confirmation"]),
                ]
            )
            values["dispatch_count"] = dispatch_count
        return values

    @http.route(
        ["/my/dispatches", "/my/dispatches/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_dispatches(self, page=1, filterby=None, sortby=None, **kw):
        """List view of dispatches assigned to portal user"""
        Dispatch = request.env["trasas.dispatch.incoming"].sudo()

        # Base domain: only dispatches assigned to me
        domain = [("handler_ids", "in", [request.env.user.id])]

        # Apply filters
        if filterby == "processing":
            domain.append(("state", "=", "processing"))
        elif filterby == "waiting":
            domain.append(("state", "=", "waiting_confirmation"))
        elif filterby == "done":
            domain.append(("state", "=", "done"))
        elif filterby == "overdue":
            domain.append(("is_overdue", "=", True))

        # Count total
        dispatch_count = Dispatch.search_count(domain)

        # Pager
        from odoo.addons.portal.controllers.portal import pager as portal_pager

        pager = portal_pager(
            url="/my/dispatches",
            url_args={"filterby": filterby, "sortby": sortby},
            total=dispatch_count,
            page=page,
            step=10,
        )

        # Search with pagination
        dispatches = Dispatch.search(
            domain,
            limit=10,
            offset=pager["offset"],
            order="deadline asc, date_received desc",
        )

        values = {
            "dispatches": dispatches,
            "page_name": "dispatch",
            "pager": pager,
            "default_url": "/my/dispatches",
            "filterby": filterby,
            "sortby": sortby,
            "dispatch_count": dispatch_count,
        }
        return request.render("trasas_dispatch_management.portal_my_dispatches", values)

    @http.route(
        ["/my/dispatch/<int:dispatch_id>"], type="http", auth="user", website=True
    )
    def portal_dispatch_detail(self, dispatch_id, access_token=None, **kw):
        """Detail view of a dispatch"""
        try:
            dispatch = (
                request.env["trasas.dispatch.incoming"].sudo().browse(dispatch_id)
            )

            # Check access: must be assigned handler
            if request.env.user not in dispatch.handler_ids:
                return request.redirect("/my")

            # Issue 1 Fix: Generate access tokens for attachments
            # so portal users can download them
            attachment_tokens = {}
            if dispatch.attachment_ids:
                dispatch.attachment_ids.sudo().generate_access_token()
                for att in dispatch.attachment_ids:
                    attachment_tokens[att.id] = att.access_token

            # Also generate token for response_file if it exists
            response_file_url = False
            if dispatch.response_file:
                # Build download URL for binary field
                response_file_url = (
                    f"/web/content/{dispatch._name}/{dispatch.id}"
                    f"/response_file/{dispatch.response_filename or 'response'}?download=true"
                )

            values = {
                "dispatch": dispatch,
                "page_name": "dispatch",
                "user": request.env.user,
                "attachment_tokens": attachment_tokens,
                "response_file_url": response_file_url,
            }
            return request.render(
                "trasas_dispatch_management.portal_dispatch_detail", values
            )
        except Exception:
            return request.redirect("/my/dispatches?error=not_found")

    @http.route(
        ["/my/dispatch/<int:dispatch_id>/submit"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_dispatch_submit(self, dispatch_id, **post):
        """Submit response from portal"""
        try:
            dispatch = (
                request.env["trasas.dispatch.incoming"].sudo().browse(dispatch_id)
            )

            # Check access
            if request.env.user not in dispatch.handler_ids:
                return request.redirect("/my")

            # Handle file upload — Issue 3 Fix: preserve original filename
            response_file = post.get("response_file")
            vals = {
                "response_dispatch_number": post.get("response_dispatch_number"),
                "response_note": post.get("response_note"),
            }
            if response_file:
                import base64

                vals["response_file"] = base64.b64encode(response_file.read())
                vals["response_filename"] = response_file.filename  # preserve name

            # Update dispatch
            dispatch.write(vals)

            # Call action to change state
            dispatch.action_submit_response()

            return request.redirect(f"/my/dispatch/{dispatch_id}?message=submitted")
        except Exception as e:
            return request.redirect(f"/my/dispatch/{dispatch_id}?error={str(e)}")
