from __future__ import annotations

import subprocess
import time

import config
from tests import thermals
from tests.common import find_tool, grade_threshold, make_result, now_iso, skipped, terminate_process


def run(duration_seconds: int | None = None) -> dict:
    name = "FurMark GPU Torture"
    started_at = now_iso()
    tool = find_tool("furmark")
    if not tool:
        return skipped(name, "GPU", "FurMark executable not found. Configure config.TOOL_MANIFEST['furmark'].")
    duration = duration_seconds or config.TEST_DURATIONS_SECONDS["furmark"]
    log_path = config.OUTPUT_DIR / f"furmark_{int(time.time())}.log"
    proc = None
    samples = []
    try:
        proc = subprocess.Popen(
            [
                str(tool),
                "/width=1920",
                "/height=1080",
                "/msaa=8",
                f"/max_time={duration * 1000}",
                "/nogui",
                "/log_score",
            ],
            cwd=str(tool.parent),
        )
        deadline = time.time() + duration
        while time.time() < deadline and proc.poll() is None:
            samples.append(thermals.snapshot())
            time.sleep(min(config.TEST_DURATIONS_SECONDS["thermal_poll"], max(0.2, deadline - time.time())))
    except Exception as exc:
        return make_result(name, "GPU", config.STATUS_FAIL, notes=[f"FurMark failed to run: {exc}"], started_at=started_at)
    finally:
        if proc:
            terminate_process(proc)
    gpu_temps = [item["gpu_temp_c"] for item in samples if isinstance(item.get("gpu_temp_c"), (int, float))]
    max_temp = max(gpu_temps) if gpu_temps else None
    status = grade_threshold(max_temp, config.THRESHOLDS["furmark"]["gpu_temp_c"])
    notes = []
    if max_temp is None:
        notes.append("GPU temperature was not available. Enable HWiNFO64 shared memory for thermal grading.")
    return make_result(
        name,
        "GPU",
        status,
        metrics={"duration_seconds": duration, "max_temp_c": max_temp, "log_path": str(log_path), "thermal_samples": samples},
        notes=notes,
        started_at=started_at,
    )

