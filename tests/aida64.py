from __future__ import annotations

import csv
import subprocess
import time

import config
from tests import thermals
from tests.common import find_tool, grade_threshold, make_result, now_iso, skipped, terminate_process


def _parse_log(path):
    temps = []
    if not path.exists():
        return temps
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        for row in csv.reader(handle):
            joined = ",".join(row).lower()
            if "cpu" not in joined:
                continue
            for cell in row:
                try:
                    value = float(cell)
                except ValueError:
                    continue
                if 20 <= value <= 120:
                    temps.append(value)
    return temps


def run(duration_seconds: int | None = None) -> dict:
    name = "AIDA64 Stability"
    started_at = now_iso()
    tool = find_tool("aida64")
    if not tool:
        return skipped(name, "CPU", "AIDA64 executable not found. Configure vendor-approved URL or install it into tools/.")
    duration = duration_seconds or config.TEST_DURATIONS_SECONDS["aida64"]
    log_path = config.OUTPUT_DIR / f"aida64_{int(time.time())}.csv"
    proc = None
    samples = []
    try:
        proc = subprocess.Popen(
            [str(tool), "/SST", "CPU,FPU,Cache,Memory", "/SSTSTOP", str(max(1, duration // 60)), "/LOG", str(log_path)],
            cwd=str(tool.parent),
        )
        deadline = time.time() + duration
        while time.time() < deadline and proc.poll() is None:
            samples.append(thermals.snapshot())
            time.sleep(min(config.TEST_DURATIONS_SECONDS["thermal_poll"], max(0.2, deadline - time.time())))
    except Exception as exc:
        return make_result(name, "CPU", config.STATUS_FAIL, notes=[f"AIDA64 failed to run: {exc}"], started_at=started_at)
    finally:
        if proc:
            terminate_process(proc)

    log_temps = _parse_log(log_path)
    sample_temps = [item["cpu_temp_c"] for item in samples if isinstance(item.get("cpu_temp_c"), (int, float))]
    max_temp = max(log_temps + sample_temps) if log_temps or sample_temps else None
    status = grade_threshold(max_temp, config.THRESHOLDS["aida64"]["cpu_temp_c"])
    notes = []
    if max_temp is None:
        notes.append("AIDA64/HWiNFO temperature telemetry was unavailable.")
    return make_result(
        name,
        "CPU",
        status,
        metrics={"duration_seconds": duration, "max_temp_c": max_temp, "log_path": str(log_path), "thermal_samples": samples},
        notes=notes,
        started_at=started_at,
    )

