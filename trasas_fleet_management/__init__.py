# -*- coding: utf-8 -*-
from . import models


def _post_init_trasas_fleet_states(env):
    """
    Đổi tên các trạng thái gốc của Fleet sang tiếng Việt,
    và ẩn (fold) các trạng thái không dùng (To Order, Downgraded).
    Chạy sau khi module được cài đặt/nâng cấp.
    """
    # Đổi tên "New Request" → "Phương tiện mới"
    state_new = env.ref(
        "fleet.fleet_vehicle_state_new_request", raise_if_not_found=False
    )
    if state_new:
        state_new.write({"name": "Phương tiện mới", "sequence": 1})

    # Đổi tên "Registered" → "Đang sử dụng"
    state_registered = env.ref(
        "fleet.fleet_vehicle_state_registered", raise_if_not_found=False
    )
    if state_registered:
        state_registered.write({"name": "Đang sử dụng", "sequence": 15})

    # Ẩn "To Order" - fold + đẩy cuối
    state_to_order = env.ref(
        "fleet.fleet_vehicle_state_to_order", raise_if_not_found=False
    )
    if state_to_order:
        state_to_order.write({"fold": True, "sequence": 998})

    # Ẩn "Downgraded" - fold + đẩy cuối
    state_downgraded = env.ref(
        "fleet.fleet_vehicle_state_downgraded", raise_if_not_found=False
    )
    if state_downgraded:
        state_downgraded.write({"fold": True, "sequence": 999})
