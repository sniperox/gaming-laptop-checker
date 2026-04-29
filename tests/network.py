from __future__ import annotations

import json
import shutil

import config
from tests.common import ensure_list, grade_threshold, is_windows, make_result, now_iso, powershell_json, run_command, skipped


def _adapter_info() -> list[dict]:
    if not is_windows():
        return []
    try:
        adapters = ensure_list(
            powershell_json(
                "Get-CimInstance Win32_NetworkAdapter | Where-Object {$_.NetEnabled -eq $true} | "
                "Select-Object Name,MACAddress,Speed,AdapterType",
                timeout=30,
            )
        )
        return adapters
    except Exception:
        return []


def run() -> dict:
    name = "Wi-Fi Speed"
    started_at = now_iso()
    metrics = {"adapters": _adapter_info()}
    command = shutil.which("speedtest-cli") or shutil.which("speedtest")
    if not command:
        return skipped(name, "Network", "speedtest-cli command not found after dependency installation.", metrics=metrics)
    try:
        completed = run_command([command, "--json"], timeout=180)
        if completed.returncode != 0:
            return skipped(name, "Network", completed.stderr.strip() or completed.stdout.strip(), metrics=metrics)
        data = json.loads(completed.stdout)
        download_mbps = round((data.get("download") or 0) / 1_000_000, 2)
        upload_mbps = round((data.get("upload") or 0) / 1_000_000, 2)
        metrics.update(
            {
                "download_mbps": download_mbps,
                "upload_mbps": upload_mbps,
                "ping_ms": data.get("ping"),
                "server": data.get("server", {}).get("sponsor"),
            }
        )
        status = grade_threshold(download_mbps, config.THRESHOLDS["network"]["download_mbps"])
        return make_result(name, "Network", status, metrics=metrics, started_at=started_at)
    except Exception as exc:
        return skipped(name, "Network", f"Speed test failed: {exc}", metrics=metrics)

