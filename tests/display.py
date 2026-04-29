from __future__ import annotations

import config
from tests.common import ensure_list, is_windows, make_result, now_iso, powershell_json, skipped


def run() -> dict:
    name = "Display"
    started_at = now_iso()
    if not is_windows():
        return skipped(name, "System", "Display WMI inventory is available on Windows only.")
    try:
        controllers = ensure_list(
            powershell_json(
                "Get-CimInstance Win32_VideoController | Select-Object "
                "Name,CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate,CurrentBitsPerPixel",
                timeout=30,
            )
        )
        displays = []
        for item in controllers:
            width = item.get("CurrentHorizontalResolution")
            height = item.get("CurrentVerticalResolution")
            displays.append(
                {
                    "adapter": item.get("Name"),
                    "resolution": f"{width}x{height}" if width and height else None,
                    "refresh_hz": item.get("CurrentRefreshRate"),
                    "color_depth": item.get("CurrentBitsPerPixel"),
                }
            )
        return make_result(name, "System", config.STATUS_PASS, metrics={"displays": displays}, started_at=started_at)
    except Exception as exc:
        return skipped(name, "System", f"Display information unavailable: {exc}")

