/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DocumentsDetailsPanel } from "@documents/components/documents_details_panel/documents_details_panel";
import { SelectionField } from "@web/views/fields/selection/selection_field";
import { DateTimeField } from "@web/views/fields/datetime/datetime_field";
import { IntegerField } from "@web/views/fields/integer/integer_field";
import { ConfidentialLevelField } from "./confidential_level_field";

// Thêm các thành phần UI (fields) còn thiếu của Odoo core vào DocumentsDetailsPanel
// để dùng được trong file XML (documents_details_panel_trasas.xml)
patch(DocumentsDetailsPanel.components, {
    SelectionField,
    DateTimeField,
    IntegerField,
    ConfidentialLevelField,
});

// Patch prototype để thêm method onRequestAccess
patch(DocumentsDetailsPanel.prototype, {
    async onRequestAccess() {
        const recordId = this.record.resId;
        if (!recordId) return;
        const result = await this.env.services.orm.call(
            "documents.document",
            "action_request_access",
            [recordId],
        );
        if (result) {
            this.env.services.action.doAction(result);
        }
    },
});
