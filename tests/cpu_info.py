from __future__ import annotations

import cpuinfo

import config
from tests.common import is_windows, make_result, now_iso, powershell_json, skipped


def run() -> dict:
    name = "CPU Info"
    started_at = now_iso()
    metrics = {}
    notes = []
    try:
        if is_windows():
            data = powershell_json(
                "Get-CimInstance Win32_Processor | Select-Object -First 1 "
                "Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,CurrentClockSpeed,L2CacheSize,L3CacheSize",
                timeout=30,
            )
            metrics = {
                "model": data.get("Name"),
                "cores": data.get("NumberOfCores"),
                "threads": data.get("NumberOfLogicalProcessors"),
                "max_clock_mhz": data.get("MaxClockSpeed"),
                "current_clock_mhz": data.get("CurrentClockSpeed"),
                "l2_cache_kb": data.get("L2CacheSize"),
                "l3_cache_kb": data.get("L3CacheSize"),
            }
        else:
            info = cpuinfo.get_cpu_info()
            metrics = {
                "model": info.get("brand_raw"),
                "cores": info.get("count"),
                "arch": info.get("arch"),
            }
            notes.append("Detailed WMI CPU data is Windows-only.")
        return make_result(name, "System", config.STATUS_PASS, metrics=metrics, notes=notes, started_at=started_at)
    except Exception as exc:
        return skipped(name, "System", f"CPU information unavailable: {exc}")

