from __future__ import annotations

import subprocess
import time

import config
from tests import thermals
from tests.common import find_tool, grade_threshold, make_result, now_iso, skipped, terminate_process, worst_status


def run(duration_seconds: int | None = None) -> dict:
    name = "Prime95 Small FFTs"
    started_at = now_iso()
    tool = find_tool("prime95")
    if not tool:
        return skipped(name, "CPU", "Prime95 executable not found. Run option 8 or configure config.TOOL_MANIFEST['prime95'].")

    duration = duration_seconds or config.TEST_DURATIONS_SECONDS["prime95"]
    proc = None
    samples = []
    try:
        proc = subprocess.Popen([str(tool), "-t"], cwd=str(tool.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + duration
        while time.time() < deadline:
            samples.append(thermals.snapshot())
            time.sleep(min(config.TEST_DURATIONS_SECONDS["thermal_poll"], max(0.2, deadline - time.time())))
    except Exception as exc:
        return make_result(name, "CPU", config.STATUS_FAIL, notes=[f"Prime95 failed to run: {exc}"], started_at=started_at)
    finally:
        if proc:
            terminate_process(proc)

    cpu_temps = [item["cpu_temp_c"] for item in samples if isinstance(item.get("cpu_temp_c"), (int, float))]
    cpu_clocks = [item["cpu_clock_mhz"] for item in samples if isinstance(item.get("cpu_clock_mhz"), (int, float))]
    max_temp = max(cpu_temps) if cpu_temps else None
    avg_clock = round(sum(cpu_clocks) / len(cpu_clocks), 1) if cpu_clocks else None
    throttle_pct = None
    if len(cpu_clocks) >= 2 and max(cpu_clocks) > 0:
        throttle_pct = round((max(cpu_clocks) - min(cpu_clocks)) / max(cpu_clocks) * 100, 2)

    temp_status = grade_threshold(max_temp, config.THRESHOLDS["prime95"]["cpu_temp_c"])
    throttle_status = grade_threshold(throttle_pct, config.THRESHOLDS["prime95"]["throttle_pct"])
    status = worst_status([temp_status, throttle_status])
    notes = []
    if max_temp is None:
        notes.append("CPU temperature was not available. Enable HWiNFO64 shared memory for thermal grading.")
    if throttle_pct is None:
        notes.append("CPU clock telemetry was not available. Throttle percentage could not be graded.")
    return make_result(
        name,
        "CPU",
        status,
        metrics={
            "duration_seconds": duration,
            "max_temp_c": max_temp,
            "throttle_pct": throttle_pct,
            "avg_clock_mhz": avg_clock,
            "thermal_samples": samples,
        },
        notes=notes,
        started_at=started_at,
    )

