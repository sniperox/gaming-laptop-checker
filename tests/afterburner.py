from __future__ import annotations

import config
from tests.common import find_tool, make_result, now_iso, skipped


def run() -> dict:
    name = "MSI Afterburner"
    started_at = now_iso()
    tool = find_tool("afterburner")
    if not tool:
        return skipped(name, "GPU", "MSI Afterburner executable not found. GPU clocks will use HWiNFO if available.")
    return make_result(
        name,
        "GPU",
        config.STATUS_PASS,
        metrics={"tool_path": str(tool)},
        notes=["Afterburner is available. Configure its logging path if you want CSV import in reports."],
        started_at=started_at,
    )

