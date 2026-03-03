/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DocumentsKanbanController } from "@documents/views/kanban/documents_kanban_controller";
import { DocumentsListController } from "@documents/views/list/documents_list_controller";

const highlightButtonsPatch = {
    getTopBarActionMenuItems() {
        // Get the standard items
        const items = super.getTopBarActionMenuItems(...arguments);

        // Check if any selected record is restricted
        const isRestricted = this.targetRecords.some(r => r.data.confidential_level === 'restricted');

        if (isRestricted) {
            // Apply bright highlight class for "share" and "freeze and share" buttons
            const highlightClass = 'btn-warning text-uppercase fw-bold text-dark';

            if (items.share) {
                items.share.cssClass = highlightClass;
            }
            if (items.share_frozen) {
                items.share_frozen.cssClass = highlightClass;
            }

            // Catch any embedded actions that might contain "Share"
            for (const key in items) {
                if (items[key].description && items[key].description.toString().toLowerCase().includes("share")) {
                    items[key].cssClass = highlightClass;
                }
            }
        }

        return items;
    }
};

patch(DocumentsKanbanController.prototype, highlightButtonsPatch);
if (DocumentsListController) {
    patch(DocumentsListController.prototype, highlightButtonsPatch);
}
