from __future__ import annotations

import json
import re

import config
from tests.common import find_tool, grade_threshold, make_result, now_iso, run_command, skipped, worst_status


def _parse_scores(path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        data = json.loads(text)
        return {
            "single_core": data.get("score") or data.get("single_core_score"),
            "multi_core": data.get("multicore_score") or data.get("multi_core_score"),
        }
    except json.JSONDecodeError:
        pass
    single = re.search(r"single.*?([0-9]{3,6})", text, flags=re.IGNORECASE | re.DOTALL)
    multi = re.search(r"multi.*?([0-9]{3,6})", text, flags=re.IGNORECASE | re.DOTALL)
    return {
        "single_core": float(single.group(1)) if single else None,
        "multi_core": float(multi.group(1)) if multi else None,
    }


def run() -> dict:
    name = "Geekbench 6"
    started_at = now_iso()
    tool = find_tool("geekbench")
    if not tool:
        return skipped(name, "Performance", "Geekbench executable not found. Configure config.TOOL_MANIFEST['geekbench'].")
    result_path = config.OUTPUT_DIR / "geekbench_result.json"
    completed = run_command(
        [str(tool), "--upload-results", "no", "--export-json", str(result_path)],
        timeout=15 * 60,
        cwd=tool.parent,
    )
    scores = _parse_scores(result_path)
    statuses = [
        grade_threshold(scores.get("single_core"), config.THRESHOLDS["geekbench"]["single_core"]),
        grade_threshold(scores.get("multi_core"), config.THRESHOLDS["geekbench"]["multi_core"]),
    ]
    notes = []
    if completed.returncode != 0:
        notes.append(completed.stderr.strip() or "Geekbench returned a non-zero exit code.")
    return make_result(
        name,
        "Performance",
        worst_status(statuses),
        metrics={**scores, "result_path": str(result_path)},
        notes=notes,
        raw=(completed.stdout + completed.stderr)[-4000:],
        started_at=started_at,
    )

