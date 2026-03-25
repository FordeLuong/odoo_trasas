# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class OutgoingDispatchPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        """Add outgoing dispatch count to portal homepage"""
        values = super()._prepare_home_portal_values(counters)
        if "outgoing_dispatch_count" in counters or "dispatch_count" in counters:
            # Count outgoing dispatches assigned to current user (as drafter)
            outgoing_count = request.env["trasas.dispatch.outgoing"].search_count(
                [
                    ("drafter_id", "=", request.env.user.id),
                    ("state", "=", "draft"),
                ]
            )
            values["outgoing_dispatch_count"] = outgoing_count
        return values

    @http.route(
        ["/my/outgoing_dispatches", "/my/outgoing_dispatches/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_outgoing_dispatches(self, page=1, filterby=None, sortby=None, **kw):
        """List view of outgoing dispatches for portal user"""
        OutgoingDispatch = request.env["trasas.dispatch.outgoing"].sudo()

        # Base domain: only dispatches drafted by me
        domain = [("drafter_id", "=", request.env.user.id)]

        # Apply filters
        if filterby == "draft":
            domain.append(("state", "=", "draft"))
        elif filterby == "waiting_approval":
            domain.append(("state", "=", "waiting_approval"))
        elif filterby == "to_promulgate":
            domain.append(("state", "=", "to_promulgate"))
        elif filterby == "sent":
            domain.append(("state", "=", "sent"))

        # Count total
        dispatch_count = OutgoingDispatch.search_count(domain)

        # Pager
        from odoo.addons.portal.controllers.portal import pager as portal_pager

        pager = portal_pager(
            url="/my/outgoing_dispatches",
            url_args={"filterby": filterby, "sortby": sortby},
            total=dispatch_count,
            page=page,
            step=10,
        )

        # Search with pagination
        dispatches = OutgoingDispatch.search(
            domain,
            limit=10,
            offset=pager["offset"],
            order="create_date desc",
        )

        values = {
            "outgoing_dispatches": dispatches,
            "page_name": "outgoing_dispatch",
            "pager": pager,
            "default_url": "/my/outgoing_dispatches",
            "filterby": filterby,
            "sortby": sortby,
            "outgoing_dispatch_count": dispatch_count,
        }
        return request.render(
            "trasas_dispatch_outgoing.portal_my_outgoing_dispatches", values
        )

    @http.route(
        ["/my/outgoing_dispatch/<int:dispatch_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_outgoing_dispatch_detail(self, dispatch_id, access_token=None, **kw):
        """Detail view of an outgoing dispatch"""
        try:
            dispatch = (
                request.env["trasas.dispatch.outgoing"].sudo().browse(dispatch_id)
            )

            # Check access: must be the drafter
            if request.env.user.id != dispatch.drafter_id.id:
                return request.redirect("/my")

            # Download URLs for files
            draft_file_url = False
            if dispatch.draft_file:
                draft_file_url = (
                    f"/web/content/{dispatch._name}/{dispatch.id}"
                    f"/draft_file/{dispatch.draft_filename or 'draft'}?download=true"
                )

            official_file_url = False
            if dispatch.official_file:
                official_file_url = (
                    f"/web/content/{dispatch._name}/{dispatch.id}"
                    f"/official_file/{dispatch.official_filename or 'official'}?download=true"
                )

            # Lấy danh sách Người duyệt (Ban Giám đốc)
            group_approver = request.env.ref("trasas_dispatch_management.group_dispatch_approver", raise_if_not_found=False)
            approvers = request.env["res.users"].sudo().search([("group_ids", "in", [group_approver.id])]) if group_approver else []

            values = {
                "dispatch": dispatch,
                "page_name": "outgoing_dispatch",
                "user": request.env.user,
                "draft_file_url": draft_file_url,
                "official_file_url": official_file_url,
                "approvers": approvers,
            }
            return request.render(
                "trasas_dispatch_outgoing.portal_outgoing_dispatch_detail", values
            )
        except Exception:
            return request.redirect("/my/outgoing_dispatches?error=not_found")

    @http.route(
        ["/my/outgoing_dispatch/<int:dispatch_id>/submit"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_outgoing_dispatch_submit(self, dispatch_id, **post):
        """Submit draft file from portal"""
        try:
            dispatch = (
                request.env["trasas.dispatch.outgoing"].sudo().browse(dispatch_id)
            )

            # Check access
            if request.env.user.id != dispatch.drafter_id.id:
                return request.redirect("/my")

            # Handle file upload
            draft_file = post.get("draft_file")
            vals = {}
            if draft_file:
                import base64

                vals["draft_file"] = base64.b64encode(draft_file.read())
                vals["draft_filename"] = draft_file.filename

            # Handle approver selection
            approver_id = post.get("approver_id")
            if approver_id:
                vals["approver_id"] = int(approver_id)

            if vals:
                dispatch.write(vals)

            # Trigger submit action if it's currently in draft
            if dispatch.state == "draft":
                dispatch.action_submit()

            return request.redirect(
                f"/my/outgoing_dispatch/{dispatch_id}?message=submitted"
            )
        except Exception as e:
            return request.redirect(
                f"/my/outgoing_dispatch/{dispatch_id}?error={str(e)}"
            )

    @http.route(
        ["/my/outgoing_dispatch/<int:dispatch_id>/send_to_hcns"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_outgoing_dispatch_send_to_hcns(self, dispatch_id, **post):
        """Người soạn gửi CV đi cho HCNS ban hành (từ trạng thái Đã duyệt)"""
        try:
            dispatch = (
                request.env["trasas.dispatch.outgoing"].sudo().browse(dispatch_id)
            )
            if request.env.user.id != dispatch.drafter_id.id:
                return request.redirect("/my")

            if dispatch.state == "approved":
                dispatch.action_send_to_hcns()

            return request.redirect(
                f"/my/outgoing_dispatch/{dispatch_id}?message=sent_to_hcns"
            )
        except Exception as e:
            return request.redirect(
                f"/my/outgoing_dispatch/{dispatch_id}?error={str(e)}"
            )

    @http.route(
        ["/my/outgoing_dispatch/<int:dispatch_id>/send"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_outgoing_dispatch_send(self, dispatch_id, **post):
        """Người soạn gửi CV đi cho đối tác (từ trạng thái Đã phát hành)"""
        try:
            dispatch = (
                request.env["trasas.dispatch.outgoing"].sudo().browse(dispatch_id)
            )
            if request.env.user.id != dispatch.drafter_id.id:
                return request.redirect("/my")

            if dispatch.state == "released":
                dispatch.action_send()

            return request.redirect(f"/my/outgoing_dispatch/{dispatch_id}?message=sent")
        except Exception as e:
            return request.redirect(
                f"/my/outgoing_dispatch/{dispatch_id}?error={str(e)}"
            )
    @http.route(
        ["/my/outgoing_dispatch/<int:dispatch_id>/no_response"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_outgoing_dispatch_no_response(self, dispatch_id, **post):
        """Hủy công văn đi và hoàn thành công văn đến gốc (Không cần phản hồi)"""
        try:
            dispatch = (
                request.env["trasas.dispatch.outgoing"].sudo().browse(dispatch_id)
            )
            if request.env.user.id != dispatch.drafter_id.id:
                return request.redirect("/my")

            if dispatch.state == "draft":
                dispatch.action_no_response_needed()

            return request.redirect("/my/outgoing_dispatches?message=no_response_done")
        except Exception as e:
            return request.redirect(
                f"/my/outgoing_dispatch/{dispatch_id}?error={str(e)}"
            )
