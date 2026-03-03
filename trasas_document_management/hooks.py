# -*- coding: utf-8 -*-


def post_migrate(env):
    """Sau mỗi lần upgrade module, đảm bảo tất cả workspace root (folder_id = False)
    đều có access_internal = 'edit' để mọi internal user có thể thấy và upload file.
    """
    root_folders = (
        env["documents.document"]
        .with_context(active_test=False)
        .search(
            [
                ("type", "=", "folder"),
                ("folder_id", "=", False),
                ("access_internal", "!=", "edit"),
            ]
        )
    )
    if root_folders:
        root_folders.sudo().write({"access_internal": "edit"})
