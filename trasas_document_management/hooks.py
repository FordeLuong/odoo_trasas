# -*- coding: utf-8 -*-


def post_init_hook(env):
    """Gọi post_migrate khi install lần đầu"""
    post_migrate(env)


def post_migrate(env):
    """Sau mỗi lần upgrade module, đảm bảo TẤT CẢ folders
    đều có access_internal = 'edit' để mọi internal user có thể thấy và upload file.
    """
    folders = (
        env["documents.document"]
        .with_context(active_test=False)
        .search(
            [
                ("type", "=", "folder"),
                ("access_internal", "!=", "edit"),
            ]
        )
    )
    if folders:
        folders.sudo().write({"access_internal": "edit"})
