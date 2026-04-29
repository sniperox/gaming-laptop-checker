from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import config
from tests.common import find_tool, grade_threshold, make_result, now_iso, run_command, skipped


def _parse_score(path) -> float | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        root = ET.fromstring(text)
        for elem in root.iter():
            if "score" in elem.tag.lower() and elem.text:
                numeric = re.sub(r"[^0-9.]", "", elem.text)
                if numeric:
                    return float(numeric)
    except Exception:
        pass
    match = re.search(r"score.*?([0-9]{3,6})", text, flags=re.IGNORECASE | re.DOTALL)
    return float(match.group(1)) if match else None


def run() -> dict:
    name = "PCMark 10"
    started_at = now_iso()
    tool = find_tool("pcmark10")
    if not tool:
        return skipped(name, "Performance", "PCMark 10 command-line executable not found.")
    result_path = config.OUTPUT_DIR / "pcmark10_result.xml"
    completed = run_command([str(tool), "--definition=pcmark10", f"--out={result_path}"], timeout=20 * 60, cwd=tool.parent)
    score = _parse_score(result_path)
    status = grade_threshold(score, config.THRESHOLDS["pcmark10"]["score"])
    if completed.returncode != 0 and score is None:
        status = config.STATUS_FAIL
    return make_result(
        name,
        "Performance",
        status,
        metrics={"score": score, "result_path": str(result_path)},
        raw=(completed.stdout + completed.stderr)[-4000:],
        started_at=started_at,
    )

