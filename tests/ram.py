from __future__ import annotations

import config
from tests.common import ensure_list, grade_threshold, is_windows, make_result, now_iso, powershell_json, skipped, worst_status


MEMORY_TYPES = {
    20: "DDR",
    21: "DDR2",
    24: "DDR3",
    26: "DDR4",
    34: "DDR5",
}


def run() -> dict:
    name = "RAM"
    started_at = now_iso()
    if not is_windows():
        return skipped(name, "System", "RAM WMI inventory is available on Windows only.")
    try:
        modules = ensure_list(
            powershell_json(
                "Get-CimInstance Win32_PhysicalMemory | Select-Object "
                "Capacity,Speed,ConfiguredClockSpeed,SMBIOSMemoryType,Manufacturer,PartNumber,DeviceLocator",
                timeout=30,
            )
        )
        normalized = []
        speeds = []
        total_bytes = 0
        for module in modules:
            total_bytes += int(module.get("Capacity") or 0)
            speed = module.get("ConfiguredClockSpeed") or module.get("Speed")
            if speed:
                speeds.append(int(speed))
            normalized.append(
                {
                    "slot": module.get("DeviceLocator"),
                    "capacity_gb": round((module.get("Capacity") or 0) / (1024**3), 2),
                    "speed_mhz": speed,
                    "type": MEMORY_TYPES.get(module.get("SMBIOSMemoryType"), module.get("SMBIOSMemoryType")),
                    "manufacturer": module.get("Manufacturer"),
                    "part_number": str(module.get("PartNumber") or "").strip(),
                }
            )
        effective_speed = min(speeds) if speeds else None
        speed_status = grade_threshold(effective_speed, config.THRESHOLDS["ram"]["speed_mhz"])
        status = worst_status([speed_status])
        notes = []
        if effective_speed is None:
            notes.append("RAM speed was not reported by WMI.")
        return make_result(
            name,
            "System",
            status,
            metrics={
                "total_gb": round(total_bytes / (1024**3), 2),
                "module_count": len(normalized),
                "effective_speed_mhz": effective_speed,
                "modules": normalized,
            },
            notes=notes,
            started_at=started_at,
        )
    except Exception as exc:
        return skipped(name, "System", f"RAM information unavailable: {exc}")

