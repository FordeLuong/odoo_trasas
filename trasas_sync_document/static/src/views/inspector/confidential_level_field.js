/** @odoo-module **/

import { Component } from "@odoo/owl";
import { SelectionField } from "@web/views/fields/selection/selection_field";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

/**
 * Wrapper OWL component cho field confidential_level.
 * Intercept onChange để hiện popup xác nhận trước khi commit giá trị.
 */
export class ConfidentialLevelField extends SelectionField {
    static template = SelectionField.template;

    setup() {
        super.setup();
        this.dialog = useService("dialog");
    }

    onChange(value) {
        const oldValue = this.props.record.data[this.props.name];

        if (value === "public") {
            // Popup xác nhận khi chuyển sang Công khai
            this.dialog.add(ConfirmationDialog, {
                title: "Xác nhận chia sẻ công khai",
                body: "File này sẽ được chia sẻ với tất cả mọi người. Bạn có chắc chắn?",
                confirm: () => {
                    super.onChange(value);
                },
                cancel: () => {
                    // Không làm gì — giữ nguyên giá trị cũ
                },
            });
        } else if (value === "restricted") {
            // Popup thông báo khi chuyển sang Giới hạn
            // Commit giá trị trước, sau đó hiện thông báo
            super.onChange(value);
            this.dialog.add(ConfirmationDialog, {
                title: "Thông báo",
                body: "Vui lòng nhấn Share ở trên để chia sẻ cho người khác.",
                confirmLabel: "Đã hiểu",
            });
        } else {
            // "only me" hoặc các giá trị khác — commit bình thường
            super.onChange(value);
        }
    }
}
