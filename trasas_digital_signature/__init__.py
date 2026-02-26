# -*- coding: utf-8 -*-
import os
import sys


def _reconfigure_stdio_utf8_on_windows() -> None:
    if os.name != "nt":
        return
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass


_reconfigure_stdio_utf8_on_windows()

from . import models  # noqa: E402
from . import controllers  # noqa: E402
