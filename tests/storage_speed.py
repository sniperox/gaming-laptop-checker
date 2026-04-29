from __future__ import annotations

import re

import config
from tests.common import grade_threshold, is_windows, make_result, now_iso, run_command, skipped, worst_status


def _parse_winsat(text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for line in text.splitlines():
        lower = line.lower()
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s+mb/s", lower)
        if not match:
            continue
        value = float(match.group(1))
        if "sequential" in lower and "read" in lower:
            metrics["seq_read_mbps"] = value
        elif "sequential" in lower and "write" in lower:
            metrics["seq_write_mbps"] = value
        elif "random" in lower and "read" in lower:
            metrics["random_4k_read_mbps"] = value
        elif "random" in lower and "write" in lower:
            metrics["random_4k_write_mbps"] = value
    return metrics


def run(drive: str = "C") -> dict:
    name = "Storage Speed"
    started_at = now_iso()
    if not is_windows():
        return skipped(name, "Storage", "Storage speed benchmark is available on Windows only.")
    completed = run_command(["winsat", "disk", "-drive", drive.rstrip(":")], timeout=420)
    if completed.returncode != 0:
        return skipped(name, "Storage", completed.stderr.strip() or completed.stdout.strip())
    metrics = _parse_winsat(completed.stdout)
    statuses = [
        grade_threshold(metrics.get("seq_read_mbps"), config.THRESHOLDS["storage"]["seq_read_mbps"]),
        grade_threshold(metrics.get("random_4k_read_mbps"), config.THRESHOLDS["storage"]["random_4k_read_mbps"]),
    ]
    notes = ["Used built-in WinSAT disk benchmark. Configure CrystalDiskMark in config.py for vendor-specific output."]
    return make_result(name, "Storage", worst_status(statuses), metrics=metrics, notes=notes, started_at=started_at)

