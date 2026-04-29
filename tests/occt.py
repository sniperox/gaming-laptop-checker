from __future__ import annotations

import re

import config
from tests.common import find_tool, grade_threshold, make_result, now_iso, run_command, skipped


def _parse_errors(text: str) -> int:
    matches = re.findall(r"(\d+)\s+errors?", text, flags=re.IGNORECASE)
    if matches:
        return max(int(item) for item in matches)
    if "error" in text.lower() and "0 error" not in text.lower():
        return 1
    return 0


def _run_occt(test_name: str, occt_mode: str, duration: int) -> dict:
    started_at = now_iso()
    tool = find_tool("occt")
    if not tool:
        return skipped(test_name, "Stability", "OCCT executable not found. Configure config.TOOL_MANIFEST['occt'].")
    log_path = config.OUTPUT_DIR / f"occt_{occt_mode.lower()}.log"
    completed = run_command(
        [str(tool), f"/test:{occt_mode}", f"/time:{duration}", "/autostop", f"/log:{log_path}"],
        timeout=duration + 120,
        cwd=tool.parent,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    if log_path.exists():
        output += "\n" + log_path.read_text(encoding="utf-8", errors="ignore")
    errors = _parse_errors(output)
    status = grade_threshold(errors, config.THRESHOLDS["occt"]["errors"])
    if completed.returncode != 0 and errors == 0:
        status = config.STATUS_FAIL
    return make_result(
        test_name,
        "Stability",
        status,
        metrics={"duration_seconds": duration, "errors": errors, "returncode": completed.returncode, "log_path": str(log_path)},
        raw=output[-4000:],
        started_at=started_at,
    )


def run_cpu() -> dict:
    return _run_occt("OCCT CPU", "CPU", config.TEST_DURATIONS_SECONDS["occt_cpu"])


def run_gpu() -> dict:
    return _run_occt("OCCT GPU", "GPU", config.TEST_DURATIONS_SECONDS["occt_gpu"])


def run_memory() -> dict:
    return _run_occt("OCCT Memory", "MEMORY", config.TEST_DURATIONS_SECONDS["occt_memory"])

