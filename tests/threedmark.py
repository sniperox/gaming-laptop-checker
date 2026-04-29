from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import config
from tests.common import find_tool, grade_threshold, make_result, now_iso, run_command, skipped, worst_status


BENCHMARKS = {
    "fire_strike": "Fire Strike",
    "time_spy": "Time Spy",
    "port_royal": "Port Royal",
    "speed_way": "Speed Way",
}


def _parse_score(path) -> float | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        root = ET.fromstring(text)
        for elem in root.iter():
            if elem.tag.lower().endswith("score") and elem.text:
                return float(re.sub(r"[^0-9.]", "", elem.text))
    except Exception:
        pass
    match = re.search(r"(?:score|3dmark score).*?([0-9]+)", text, flags=re.IGNORECASE | re.DOTALL)
    return float(match.group(1)) if match else None


def run() -> dict:
    name = "3DMark"
    started_at = now_iso()
    tool = find_tool("3dmark")
    if not tool:
        return skipped(name, "GPU", "3DMark command-line executable not found. Install 3DMark and ensure 3DMarkCmd.exe is visible.")
    results = {}
    statuses = []
    for key, display in BENCHMARKS.items():
        xml_path = config.OUTPUT_DIR / f"3dmark_{key}.xml"
        completed = run_command(
            [str(tool), f"--benchmark={display}", f"--out={xml_path}"],
            timeout=30 * 60,
            cwd=tool.parent,
        )
        score = _parse_score(xml_path)
        status = grade_threshold(score, config.THRESHOLDS["3dmark"][key])
        if completed.returncode != 0 and score is None:
            status = config.STATUS_FAIL
        statuses.append(status)
        results[key] = {
            "name": display,
            "score": score,
            "status": status,
            "result_path": str(xml_path),
            "returncode": completed.returncode,
        }
    return make_result(name, "GPU", worst_status(statuses), metrics={"benchmarks": results}, started_at=started_at)

