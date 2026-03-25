from odoo import http, _, fields
from odoo.exceptions import UserError
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

            # Find PDF attachment specifically for digital signing
            contract_pdf_attachments = request.env["ir.attachment"].sudo().search([
                ("res_model", "=", "trasas.contract"),
                ("res_id", "=", contract_sudo.id),
                ("mimetype", "like", "application/pdf"),
            ])
            if not contract_pdf_attachments:
                contract_pdf_attachments = attachments

            # Lấy yêu cầu ký số đang hoạt động (mới nhất, không phải cancelled/expired)
            active_sign_request = request.env["trasas.signature.request"].sudo().search([
                ("contract_id", "=", contract_sudo.id),
                ("state", "not in", ["cancelled", "expired"]),
            ], order="id desc", limit=1)

            # Stages for the workflow stepper
            stages = [
                ("draft", "Nháp"),
                ("in_review", "Rà soát"),
                ("waiting", "Chờ duyệt"),
                ("approved", "Đã duyệt"),
                ("signing", "Đang ký"),
                ("signed", "Đã ký"),
            ]

            # Chuẩn bị người ký mặc định để hiển thị form nhập CCCD trên Portal
            default_signers = []
            signature_providers = []
            if contract_sudo.state in ['approved', 'signing'] and contract_sudo.signing_method == 'digital':
                raw_signers = contract_sudo._prepare_default_signers()
                for _, _, vals in raw_signers:
                    default_signers.append({
                        'name': vals.get('signer_name'),
                        'role': vals.get('role'),
                        'role_label': 'Nội bộ (TRASAS)',
                        'email': vals.get('signer_email'),
                    })
                
                # Lấy danh sách nhà cung cấp để chọn trên Portal
                signature_providers = request.env["trasas.signature.provider"].sudo().search([
                    ("active", "=", True)
                ], order="sequence, id")

            values = {
                "contract": contract_sudo,
                "token": access_token,
                "reviewers": reviewers,
                "approvers": approvers,
                "attachments": attachments,
                "contract_pdf_attachments": contract_pdf_attachments,
                "active_sign_request": active_sign_request,
                "default_signers": default_signers,
                "signature_providers": signature_providers,
                "stages": stages,
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
            "signing_method": post.get("signing_method") or "manual",
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
                attachment = (
                    request.env["ir.attachment"]
                    .sudo()
                    .create(
                        {
                            "name": file.filename,
                            "datas": base64.b64encode(file.read()),
                            "res_model": "trasas.contract",
                            "res_id": contract.id,
                        }
                    )
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
                    attachment = (
                        request.env["ir.attachment"]
                        .sudo()
                        .create(
                            {
                                "name": file.filename,
                                "datas": base64.b64encode(file.read()),
                                "res_model": "trasas.contract",
                                "res_id": contract.id,
                            }
                        )
                    )
                    contract.message_post(
                        body=_("File đính kèm từ Portal (Trình rà soát): %s")
                        % file.filename,
                        attachment_ids=[attachment.id],
                    )
            try:
                contract.action_submit_for_review()
                return request.redirect(
                    f"/my/contracts/{contract_id}?message=submitted_review"
                )
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
                    attachment = (
                        request.env["ir.attachment"]
                        .sudo()
                        .create(
                            {
                                "name": file.filename,
                                "datas": base64.b64encode(file.read()),
                                "res_model": "trasas.contract",
                                "res_id": contract.id,
                            }
                        )
                    )
                    contract.message_post(
                        body=_("File đính kèm từ Portal (Trình duyệt): %s")
                        % file.filename,
                        attachment_ids=[attachment.id],
                    )
            try:
                contract.action_submit_for_approval()
                return request.redirect(
                    f"/my/contracts/{contract_id}?message=submitted_approval"
                )
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
                    attachment = (
                        request.env["ir.attachment"]
                        .sudo()
                        .create(
                            {
                                "name": file.filename,
                                "datas": base64.b64encode(file.read()),
                                "res_model": "trasas.contract",
                                "res_id": contract.id,
                            }
                        )
                    )
                    contract.message_post(
                        body=_("File đính kèm từ Portal (Cập nhật): %s")
                        % file.filename,
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
                attachment = (
                    request.env["ir.attachment"]
                    .sudo()
                    .create(
                        {
                            "name": file.filename,
                            "datas": base64.b64encode(file.read()),
                            "res_model": "trasas.contract",
                            "res_id": contract.id,
                        }
                    )
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

    # ============ HELPER ============
    def _check_contract_access(self, contract):
        """Kiểm tra user hiện tại có quyền thao tác trên contract không"""
        user = request.env.user
        return contract.exists() and (
            contract.partner_id == user.partner_id or contract.user_id == user
        )

    # ============ B6-B15 SIGNING WORKFLOW ROUTES ============

    @http.route(
        ["/my/contracts/<int:contract_id>/start_signing"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_start_signing(self, contract_id, **post):
        """B6: Bắt đầu ký (approved → signing)"""
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if not self._check_contract_access(contract):
            return request.redirect("/my/contracts")
        try:
            contract.action_start_signing()
            return request.redirect(
                f"/my/contracts/{contract_id}?message=signing_started"
            )
        except Exception as e:
            return request.redirect(f"/my/contracts/{contract_id}?error={str(e)}")

    @http.route(
        ["/my/contracts/<int:contract_id>/mark_internal_signed"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_mark_internal_signed(self, contract_id, **post):
        """B11/B15: Xác nhận TRASAS đã ký (cả Luồng A và B)"""
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if not self._check_contract_access(contract):
            return request.redirect("/my/contracts")
        try:
            contract.action_mark_internal_signed()
            return request.redirect(
                f"/my/contracts/{contract_id}?message=internal_signed"
            )
        except Exception as e:
            return request.redirect(f"/my/contracts/{contract_id}?error={str(e)}")

    @http.route(
        ["/my/contracts/<int:contract_id>/mark_sent_partner"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_mark_sent_partner(self, contract_id, **post):
        """B12: Xác nhận đã gửi cho đối tác (Luồng A)"""
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if not self._check_contract_access(contract):
            return request.redirect("/my/contracts")
        try:
            # action_mark_sent_to_partner may return mail compose action, ignore on portal
            contract.action_mark_sent_to_partner()
            return request.redirect(
                f"/my/contracts/{contract_id}?message=sent_to_partner"
            )
        except Exception as e:
            return request.redirect(f"/my/contracts/{contract_id}?error={str(e)}")

    @http.route(
        ["/my/contracts/<int:contract_id>/mark_partner_signed"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_mark_partner_signed(self, contract_id, **post):
        """B14: Xác nhận đối tác đã ký"""
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if not self._check_contract_access(contract):
            return request.redirect("/my/contracts")
        try:
            contract.action_mark_partner_signed()
            return request.redirect(
                f"/my/contracts/{contract_id}?message=partner_signed"
            )
        except Exception as e:
            return request.redirect(f"/my/contracts/{contract_id}?error={str(e)}")

    @http.route(
        ["/my/contracts/<int:contract_id>/confirm_signed"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_confirm_signed(self, contract_id, **post):
        """B13: Xác nhận hoàn tất ký kết (signing → signed) - Gộp cả upload scan"""
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if not self._check_contract_access(contract):
            return request.redirect("/my/contracts")

        # Xử lý upload file nếu có (bắt buộc theo UI mới)
        file = request.httprequest.files.get("final_scan")
        if file:
            file_content = base64.b64encode(file.read())
            contract.sudo().write(
                {
                    "final_scan_file": file_content,
                    "final_scan_filename": file.filename,
                }
            )
            # Ép ghi xuống DB ngay để action_confirm_signed phía dưới nhìn thấy file
            contract.sudo().flush_recordset(["final_scan_file"])

            # Tạo attachment đồng bộ
            request.env["ir.attachment"].sudo().create(
                {
                    "name": file.filename,
                    "datas": file_content,
                    "res_model": "trasas.contract",
                    "res_id": contract.id,
                }
            )

        try:
            contract.action_confirm_signed()
            return request.redirect(
                f"/my/contracts/{contract_id}?message=signing_completed"
            )
        except Exception as e:
            return request.redirect(f"/my/contracts/{contract_id}?error={str(e)}")

    @http.route(
        ["/my/contracts/<int:contract_id>/upload_scan"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_upload_scan(self, contract_id, **post):
        """Upload bản scan hoàn tất (final_scan_file)"""
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if not self._check_contract_access(contract):
            return request.redirect("/my/contracts")

        file = request.httprequest.files.get("final_scan")
        if file:
            file_content = base64.b64encode(file.read())
            contract.write(
                {
                    "final_scan_file": file_content,
                    "final_scan_filename": file.filename,
                }
            )
            # Cũng tạo attachment để đồng bộ sang Documents
            attachment = (
                request.env["ir.attachment"]
                .sudo()
                .create(
                    {
                        "name": file.filename,
                        "datas": file_content,
                        "res_model": "trasas.contract",
                        "res_id": contract.id,
                    }
                )
            )
            contract.message_post(
                body=_("Upload bản scan hoàn tất từ Portal: %s") % file.filename,
                attachment_ids=[attachment.id],
            )
        return request.redirect(f"/my/contracts/{contract_id}?message=scan_uploaded")

    @http.route(
        ["/my/contracts/<int:contract_id>/create_sign_request"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_create_sign_request(self, contract_id, **post):
        """Tạo yêu cầu ký số (thay vì mở wizard như Backend)"""
        contract = request.env["trasas.contract"].sudo().browse(contract_id)
        if not self._check_contract_access(contract):
            return request.redirect("/my/contracts")
        try:
            # Kiểm tra xem đã có request đang active chưa (tránh tạo trùng)
            existing = request.env["trasas.signature.request"].sudo().search([
                ("contract_id", "=", contract.id),
                ("state", "not in", ["cancelled", "expired"]),
            ], limit=1)
            if existing:
                raise UserError(_(
                    "Đã có yêu cầu ký số đang xử lý (trạng thái: %s). "
                    "Vui lòng hủy yêu cầu cũ trước khi tạo yêu cầu mới."
                ) % existing.state)

            # Bắt đầu ký nếu chưa ở trạng thái signing
            if contract.state == "approved":
                contract.action_start_signing()

            # Tìm nhà cung cấp chữ ký số (ưu tiên từ form, nếu không lấy cái đầu tiên)
            provider_id = post.get('provider_id')
            if provider_id:
                provider = request.env["trasas.signature.provider"].sudo().browse(int(provider_id))
            else:
                provider = (
                    request.env["trasas.signature.provider"]
                    .sudo()
                    .search([("active", "=", True)], order="sequence, id", limit=1)
                )

            if not provider or not provider.exists():
                raise UserError(
                    _("Không tìm thấy nhà cung cấp chữ ký số nào đang hoạt động!")
                )

            # Tìm file PDF đính kèm hợp đồng (ưu tiên PDF, fallback file đầu tiên)
            attachment = request.env["ir.attachment"].sudo().search([
                ("res_model", "=", "trasas.contract"),
                ("res_id", "=", contract.id),
                ("mimetype", "like", "application/pdf"),
            ], order="id desc", limit=1)
            if not attachment:
                attachment = request.env["ir.attachment"].sudo().search([
                    ("res_model", "=", "trasas.contract"),
                    ("res_id", "=", contract.id),
                ], order="id desc", limit=1)
            if not attachment:
                raise UserError(_(
                    "Hợp đồng chưa có file đính kèm để ký số! "
                    "Vui lòng upload file hợp đồng (PDF) trước."
                ))

            # Tạo signature request trực tiếp (thay wizard)
            signer_vals = contract._prepare_default_signers()
            
            # Cập nhật CCCD từ form portal vào signer_vals
            for i, (op, flag, vals) in enumerate(signer_vals):
                id_num = post.get(f'signer_id_number_{i}')
                if id_num:
                    vals['id_number'] = id_num.strip()

            sig_request = (
                request.env["trasas.signature.request"]
                .sudo()
                .create(
                    {
                        "contract_id": contract.id,
                        "provider_id": provider.id,
                        "document_file": attachment.datas,
                        "document_filename": attachment.name,
                        "signing_flow": contract.signing_flow,
                        "deadline": contract.sign_deadline,
                        "signer_ids": signer_vals,
                    }
                )
            )
            # Gửi yêu cầu ngay lập tức để người ký nhận được email/link
            sig_request.action_send()

            return request.redirect(
                f"/my/contracts/{contract_id}?message=sign_request_created"
            )
        except Exception as e:
            return request.redirect(f"/my/contracts/{contract_id}?error={str(e)}")

    @http.route(["/my/contracts/<int:contract_id>/check_sign_status"], type="http", auth="public", website=True)
    def portal_check_sign_status(self, contract_id, access_token=None, **post):
        try:
            contract_sudo = request.env["trasas.contract"].sudo().browse(contract_id)
            if not self._check_contract_access(contract_sudo):
                return request.redirect("/my")

            # Tìm yêu cầu ký số đang hoạt động
            active_sign_request = (
                request.env["trasas.signature.request"]
                .sudo()
                .search(
                    [
                        ("contract_id", "=", contract_sudo.id),
                        ("state", "in", ["sent", "partially_signed"]),
                    ],
                    order="id desc",
                    limit=1,
                )
            )
            if active_sign_request:
                active_sign_request.action_check_status()
                return request.redirect(f"/my/contracts/{contract_id}?message=status_updated")
            
            return request.redirect(f"/my/contracts/{contract_id}")
        except Exception as e:
            return request.redirect(f"/my/contracts/{contract_id}?error={str(e)}")
