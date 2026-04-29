from __future__ import annotations

import config
from tests.common import ensure_list, is_windows, make_result, now_iso, powershell_json, skipped


def run() -> dict:
    name = "GPU Info"
    started_at = now_iso()
    if not is_windows():
        return skipped(name, "System", "GPU WMI inventory is available on Windows only.")
    try:
        data = ensure_list(
            powershell_json(
                "Get-CimInstance Win32_VideoController | Select-Object "
                "Name,AdapterRAM,DriverVersion,VideoProcessor,CurrentHorizontalResolution,"
                "CurrentVerticalResolution,CurrentRefreshRate",
                timeout=30,
            )
        )
        gpus = []
        for item in data:
            ram_bytes = item.get("AdapterRAM") or 0
            gpus.append(
                {
                    "name": item.get("Name"),
                    "vram_gb": round(ram_bytes / (1024**3), 2) if ram_bytes else None,
                    "driver": item.get("DriverVersion"),
                    "processor": item.get("VideoProcessor"),
                    "resolution": f"{item.get('CurrentHorizontalResolution')}x{item.get('CurrentVerticalResolution')}",
                    "refresh_hz": item.get("CurrentRefreshRate"),
                }
            )
        return make_result(name, "System", config.STATUS_PASS, metrics={"gpus": gpus}, started_at=started_at)
    except Exception as exc:
        return skipped(name, "System", f"GPU information unavailable: {exc}")

