/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PortalDocuments = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'click .doc-tree-toggle': '_onToggleTree',
        'click .btn-request-access': '_onRequestAccess',
        'submit #requestAccessForm': '_onSubmitRequest',
    },

    start: function () {
        this._super.apply(this, arguments);
        this._autoExpandTree();
    },

    _onToggleTree: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var toggle = ev.currentTarget;
        var targetId = toggle.getAttribute('data-target');
        var childrenEl = document.getElementById(targetId);
        if (childrenEl) {
            var isOpen = childrenEl.style.display !== 'none';
            childrenEl.style.display = isOpen ? 'none' : 'block';
            toggle.classList.toggle('open', !isOpen);
        }
    },

    _autoExpandTree: function () {
        var activeItem = this.el.querySelector('.doc-tree-item.active');
        if (activeItem) {
            var parent = activeItem.closest('.doc-tree-children');
            while (parent) {
                parent.style.display = 'block';
                var parentGroup = parent.closest('.doc-tree-group');
                if (parentGroup) {
                    var parentToggle = parentGroup.querySelector(':scope > .doc-tree-item .doc-tree-toggle');
                    if (parentToggle) {
                        parentToggle.classList.add('open');
                    }
                }
                parent = parent.parentElement ? parent.parentElement.closest('.doc-tree-children') : null;
            }
        }
    },

    _onRequestAccess: function (ev) {
        var btn = ev.currentTarget;
        var docId = btn.getAttribute('data-doc-id');
        var docName = btn.getAttribute('data-doc-name');

        var docIdInput = document.getElementById('requestDocId');
        var docNameEl = document.getElementById('requestDocName');
        var purposeEl = document.getElementById('requestPurpose');
        var modalEl = document.getElementById('requestAccessModal');

        if (!docIdInput || !modalEl) {
            console.error('Portal Documents: Modal elements not found');
            return;
        }

        docIdInput.value = docId;
        if (docNameEl) docNameEl.textContent = docName;
        if (purposeEl) purposeEl.value = '';

        // Sử dụng Bootstrap Modal qua jQuery (Odoo frontend luôn có jQuery + Bootstrap)
        $(modalEl).modal('show');
    },

    _onSubmitRequest: function (ev) {
        var purpose = document.getElementById('requestPurpose').value.trim();
        if (!purpose) {
            ev.preventDefault();
            alert('Vui lòng nhập mục đích truy cập!');
            return false;
        }
    },
});

export default publicWidget.registry.PortalDocuments;
