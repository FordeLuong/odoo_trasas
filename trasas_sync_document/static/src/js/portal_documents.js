/** @odoo-module **/

document.addEventListener('DOMContentLoaded', function () {
    // Toggle cây thư mục (mở/đóng)
    var toggles = document.querySelectorAll('.doc-tree-toggle');
    toggles.forEach(function (toggle) {
        toggle.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            var targetId = toggle.getAttribute('data-target');
            var childrenEl = document.getElementById(targetId);
            if (childrenEl) {
                var isOpen = childrenEl.style.display !== 'none';
                childrenEl.style.display = isOpen ? 'none' : 'block';
                toggle.classList.toggle('open', !isOpen);
            }
        });
    });

    // Tự động mở các thư mục cha của thư mục hiện tại (active)
    var activeItem = document.querySelector('.doc-tree-item.active');
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
});
