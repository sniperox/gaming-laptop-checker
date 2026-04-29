from __future__ import annotations

import config
from tests.common import find_tool, make_result, now_iso, skipped


def run() -> dict:
    name = "HWMonitor"
    started_at = now_iso()
    tool = find_tool("hwmonitor")
    if not tool:
        return skipped(name, "Thermals", "HWMonitor executable not found. HWiNFO telemetry remains the primary source.")
    return make_result(
        name,
        "Thermals",
        config.STATUS_PASS,
        metrics={"tool_path": str(tool)},
        notes=["HWMonitor is available. Continuous logging is handled by the thermal monitor startup step."],
        started_at=started_at,
    )

