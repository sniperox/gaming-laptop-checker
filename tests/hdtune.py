from __future__ import annotations

import config
from tests.common import find_tool, is_windows, make_result, now_iso, run_command, skipped


def run(drive: str = "C:") -> dict:
    name = "HD Tune Error Scan"
    started_at = now_iso()
    if not is_windows():
        return skipped(name, "Storage", "HD Tune scan is available on Windows only.")
    tool = find_tool("hdtune")
    if tool:
        return skipped(
            name,
            "Storage",
            "HD Tune CLI automation varies by edition. Tool was found; configure CLI flags in tests/hdtune.py if your edition supports them.",
            metrics={"tool_path": str(tool)},
        )
    completed = run_command(["chkdsk", drive, "/scan"], timeout=900)
    output = f"{completed.stdout}\n{completed.stderr}"
    lower = output.lower()
    if completed.returncode == 0 and ("no problems" in lower or "found no problems" in lower):
        status = config.STATUS_PASS
    elif completed.returncode == 0:
        status = config.STATUS_WARN
    else:
        status = config.STATUS_FAIL
    return make_result(
        name,
        "Storage",
        status,
        metrics={"drive": drive, "returncode": completed.returncode},
        notes=["HD Tune was not configured; used Windows chkdsk /scan fallback."],
        raw=output[-4000:],
        started_at=started_at,
    )

