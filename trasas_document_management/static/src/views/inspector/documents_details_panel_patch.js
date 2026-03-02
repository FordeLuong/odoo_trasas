/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DocumentsDetailsPanel } from "@documents/components/documents_details_panel/documents_details_panel";
import { SelectionField } from "@web/views/fields/selection/selection_field";
import { DateField } from "@web/views/fields/date/date_field";
import { IntegerField } from "@web/views/fields/integer/integer_field";

// Thêm các thành phần UI (fields) còn thiếu của Odoo core vào DocumentsDetailsPanel
// để dùng được trong file XML (documents_details_panel_trasas.xml)
patch(DocumentsDetailsPanel.components, {
    SelectionField,
    DateField,
    IntegerField,
});
