from odoo import http, _, fields
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request
import base64


class ContractPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "contract_count" in counters:
            contract_count = (
                request.env["trasas.contract"]
                .sudo()
                .search_count([("partner_id", "=", request.env.user.partner_id.id)])
            )
            values["contract_count"] = contract_count
        return values

    @http.route(
        ["/my/contracts", "/my/contracts/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_contracts(self, page=1, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        Contract = request.env["trasas.contract"].sudo()
        user = request.env.user

        domain = [("user_id", "=", user.id)]

        searchbar_sortings = {
            "date": {"label": _("Newest"), "order": "create_date desc"},
            "name": {"label": _("Contract Number"), "order": "name"},
            "title": {"label": _("Title"), "order": "title"},
        }
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        # count for pager
        contract_count = Contract.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/contracts",
            url_args={"sortby": sortby, "filterby": filterby},
            total=contract_count,
            page=page,
            step=10,
        )
        # content according to pager and archive selected
        contracts = Contract.search(
            domain, order=order, limit=10, offset=pager["offset"]
        )

        values.update(
            {
                "contracts": contracts,
                "page_name": "contract",
                "pager": pager,
                "default_url": "/my/contracts",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("trasas_contract_management.portal_my_contracts", values)

    @http.route(
        ["/my/contracts/<int:contract_id>"], type="http", auth="user", website=True
    )
    def portal_contract_page(self, contract_id, access_token=None, **kw):
        try:
            contract_sudo = (
                request.env["trasas.contract"].sudo().browse(contract_id).exists()
            )
            if not contract_sudo:
                return request.redirect("/my")

            # Access check: Allow if partner_id matches OR if user_id (responsible) matches
            if (
                contract_sudo.partner_id != request.env.user.partner_id
                and contract_sudo.user_id != request.env.user
            ):
                return request.redirect("/my/contracts")

            # Fetch suggested reviewers and approvers (same logic as New form)
            IrModelData = request.env["ir.model.data"].sudo()
            reviewer_data = IrModelData.search(
                [
                    ("module", "=", "trasas_contract_management"),
                    ("name", "=", "group_contract_reviewer"),
                ],
                limit=1,
            )
            approver_data = IrModelData.search(
                [
                    ("module", "=", "trasas_contract_management"),
                    ("name", "=", "group_contract_approver"),
                ],
                limit=1,
            )

            reviewer_group = (
                request.env["res.groups"].sudo().browse(reviewer_data.res_id)
                if reviewer_data
                else None
            )
            approver_group = (
                request.env["res.groups"].sudo().browse(approver_data.res_id)
                if approver_data
                else None
            )

            reviewer_ids = reviewer_group.user_ids.ids if reviewer_group else []
            approver_ids = approver_group.user_ids.ids if approver_group else []
            combined_approver_ids = list(set(reviewer_ids + approver_ids))

            reviewers = request.env["res.users"].sudo().search([("share", "=", False)])
            approvers = request.env["res.users"].sudo().browse(combined_approver_ids)

            # Fetch attachments
            attachments = request.env["ir.attachment"].sudo().search(
                [("res_model", "=", "trasas.contract"), ("res_id", "=", contract_sudo.id)]
            )

            values = {
                "contract": contract_sudo,
                "token": access_token,
                "reviewers": reviewers,
                "approvers": approvers,
                "attachments": attachments,
                "page_name": "contract",
            }
            return request.render(
                "trasas_contract_management.portal_contract_page", values
            )
        except Exception:
            return request.redirect("/my")

    @http.route(["/my/contracts/new"], type="http", auth="user", website=True)
    def portal_contract_new(self, **kw):
        contract_types = request.env["trasas.contract.type"].sudo().search([])

        # Fetch suggested reviewers and approvers based on groups
        IrModelData = request.env["ir.model.data"].sudo()
        reviewer_data = IrModelData.search(
            [
                ("module", "=", "trasas_contract_management"),
                ("name", "=", "group_contract_reviewer"),
            ],
            limit=1,
        )
        approver_data = IrModelData.search(
            [
                ("module", "=", "trasas_contract_management"),
                ("name", "=", "group_contract_approver"),
            ],
            limit=1,
        )

        reviewer_group = (
            request.env["res.groups"].sudo().browse(reviewer_data.res_id)
            if reviewer_data
            else None
        )
        approver_group = (
            request.env["res.groups"].sudo().browse(approver_data.res_id)
            if approver_data
            else None
        )

        reviewer_ids = reviewer_group.user_ids.ids if reviewer_group else []
        approver_ids = approver_group.user_ids.ids if approver_group else []

        # Combined IDs for suggested_approver_id (to match internal domain: Reviewer | Approver)
        combined_approver_ids = list(set(reviewer_ids + approver_ids))

        # All internal users for suggested_reviewer_id (to match internal: basically any user)
        # We filter out portal/public users usually, but for internal-to-internal choice, we take all res.users.
        # However, to be safe and clean, let's take all authenticated internal users.
        reviewers = request.env["res.users"].sudo().search([("share", "=", False)])
        approvers = request.env["res.users"].sudo().browse(combined_approver_ids)

        # Fetch partners (for simplicity, letting them select from all partners as requested to be like internal)
        partners = request.env["res.partner"].sudo().search([])

        values = {
            "contract_types": contract_types,
            "reviewers": reviewers,
            "approvers": approvers,
            "partners": partners,
            "page_name": "contract_new",
        }
        return request.render("trasas_contract_management.portal_contract_form", values)

    @http.route(
        ["/my/contracts/create"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_contract_create(self, **post):
        vals = {
            "title": post.get("title"),
            "contract_date": post.get("contract_date") or fields.Date.today(),
            "contract_type_id": int(post.get("contract_type_id"))
            if post.get("contract_type_id")
            else False,
            "partner_id": int(post.get("partner_id"))
            if post.get("partner_id")
            else request.env.user.partner_id.id,
            "signing_flow": post.get("signing_flow") or "trasas_first",
            "suggested_reviewer_id": int(post.get("suggested_reviewer_id"))
            if post.get("suggested_reviewer_id")
            else False,
            "suggested_approver_id": int(post.get("suggested_approver_id"))
            if post.get("suggested_approver_id")
            else False,
            "date_start": post.get("date_start"),
            "date_end": post.get("date_end"),
            "sign_deadline": post.get("sign_deadline"),
            "storage_location": post.get("storage_location"),
            "description": post.get("description"),
            "state": "draft",
            "user_id": request.env.user.id,
        }
        # Create the contract
        contract = request.env["trasas.contract"].sudo().create(vals)

        # Handle initial attachments
        attachments = request.httprequest.files.getlist("attachments")
        for file in attachments:
            if file:
                attachment = request.env["ir.attachment"].sudo().create(
                    {
                        "name": file.filename,
                        "datas": base64.b64encode(file.read()),
                        "res_model": "trasas.contract",
                        "res_id": contract.id,
                    }
                )
                contract.message_post(
                    body=_("File đính kèm ban đầu: %s") % file.filename,
                    attachment_ids=[attachment.id],
                )

        return request.redirect("/my/contracts?message=created")

    @http.route(
        ["/my/contracts/<int:contract_id>/submit_review"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_contract_submit_review(self, contract_id, **post):
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if (
            contract.exists()
            and (
                contract.partner_id == request.env.user.partner_id
                or contract.user_id == request.env.user
            )
            and contract.state == "draft"
        ):
            # Handle files from standard form
            files = request.httprequest.files.getlist("attachments")
            for file in files:
                if file:
                    attachment = request.env["ir.attachment"].sudo().create(
                        {
                            "name": file.filename,
                            "datas": base64.b64encode(file.read()),
                            "res_model": "trasas.contract",
                            "res_id": contract.id,
                        }
                    )
                    contract.message_post(
                        body=_("File đính kèm từ Portal (Trình rà soát): %s") % file.filename,
                        attachment_ids=[attachment.id],
                    )
            try:
                contract.action_submit_for_review()
                return request.redirect(f"/my/contracts/{contract_id}?message=submitted_review")
            except Exception as e:
                return request.redirect(f"/my/contracts/{contract_id}?error={str(e)}")
        return request.redirect(f"/my/contracts/{contract_id}")

    @http.route(
        ["/my/contracts/<int:contract_id>/submit_approval"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_contract_submit_approval(self, contract_id, **post):
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if (
            contract.exists()
            and (
                contract.partner_id == request.env.user.partner_id
                or contract.user_id == request.env.user
            )
            and contract.state == "draft"
        ):
            # Handle files from standard form
            files = request.httprequest.files.getlist("attachments")
            for file in files:
                if file:
                    attachment = request.env["ir.attachment"].sudo().create(
                        {
                            "name": file.filename,
                            "datas": base64.b64encode(file.read()),
                            "res_model": "trasas.contract",
                            "res_id": contract.id,
                        }
                    )
                    contract.message_post(
                        body=_("File đính kèm từ Portal (Trình duyệt): %s") % file.filename,
                        attachment_ids=[attachment.id],
                    )
            try:
                contract.action_submit_for_approval()
                return request.redirect(f"/my/contracts/{contract_id}?message=submitted_approval")
            except Exception as e:
                return request.redirect(f"/my/contracts/{contract_id}?error={str(e)}")
        return request.redirect(f"/my/contracts/{contract_id}")

    @http.route(
        ["/my/contracts/<int:contract_id>/update"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_contract_update(self, contract_id, **post):
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if (
            contract.exists()
            and contract.state == "draft"
            and (
                contract.partner_id == request.env.user.partner_id
                or contract.user_id == request.env.user
            )
        ):
            vals = {
                "suggested_reviewer_id": int(post.get("suggested_reviewer_id"))
                if post.get("suggested_reviewer_id")
                else False,
                "suggested_approver_id": int(post.get("suggested_approver_id"))
                if post.get("suggested_approver_id")
                else False,
            }
            contract.write(vals)

            # Handle files from standard form
            files = request.httprequest.files.getlist("attachments")
            for file in files:
                if file:
                    attachment = request.env["ir.attachment"].sudo().create(
                        {
                            "name": file.filename,
                            "datas": base64.b64encode(file.read()),
                            "res_model": "trasas.contract",
                            "res_id": contract.id,
                        }
                    )
                    contract.message_post(
                        body=_("File đính kèm từ Portal (Cập nhật): %s") % file.filename,
                        attachment_ids=[attachment.id],
                    )
        return request.redirect(f"/my/contracts/{contract_id}?message=updated")

    @http.route(
        ["/my/contracts/<int:contract_id>/upload"],
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def portal_contract_upload(self, contract_id, **post):
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if not contract.exists() or not (
            contract.partner_id == request.env.user.partner_id
            or contract.user_id == request.env.user
        ):
            return request.redirect("/my/contracts")

        files = request.httprequest.files.getlist("file")
        for file in files:
            if file:
                attachment = request.env["ir.attachment"].sudo().create(
                    {
                        "name": file.filename,
                        "datas": base64.b64encode(file.read()),
                        "res_model": "trasas.contract",
                        "res_id": contract.id,
                    }
                )
                contract.message_post(
                    body=_("File đính kèm mới từ Portal: %s") % file.filename,
                    attachment_ids=[attachment.id],
                )
        return request.redirect(f"/my/contracts/{contract_id}?message=updated")

    @http.route(
        ["/my/contracts/<int:contract_id>/delete_attachment/<int:attachment_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_contract_delete_attachment(self, contract_id, attachment_id, **kw):
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if (
            contract.exists()
            and contract.state == "draft"
            and (
                contract.partner_id == request.env.user.partner_id
                or contract.user_id == request.env.user
            )
        ):
            attachment = request.env["ir.attachment"].sudo().browse(attachment_id)
            if (
                attachment.exists()
                and attachment.res_model == "trasas.contract"
                and attachment.res_id == contract.id
            ):
                attachment.unlink()
        return request.redirect(f"/my/contracts/{contract_id}?message=updated")
