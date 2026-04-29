from __future__ import annotations

import json
import re

import config
from tests.common import find_tool, grade_threshold, make_result, now_iso, run_command, skipped, worst_status


def _read_score(path, names: list[str]) -> float | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        data = json.loads(text)
        for key in names:
            value = data.get(key)
            if isinstance(value, (int, float)):
                return float(value)
    except json.JSONDecodeError:
        pass
    for key in names:
        match = re.search(key + r".*?([0-9]+(?:\.[0-9]+)?)", text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return float(match.group(1))
    return None


def run() -> dict:
    name = "Cinebench R23"
    started_at = now_iso()
    tool = find_tool("cinebench")
    if not tool:
        return skipped(name, "CPU", "Cinebench executable not found. Configure config.TOOL_MANIFEST['cinebench'].")
    result_path = config.OUTPUT_DIR / "cinebench_result.json"
    completed = run_command(
        [str(tool), "--cb_num_threads=auto", f"--export_results={result_path}"],
        timeout=15 * 60,
        cwd=tool.parent,
    )
    single = _read_score(result_path, ["single_core", "single", "1T", "CPU Single"])
    multi = _read_score(result_path, ["multi_core", "multi", "nT", "CPU Multi"])
    statuses = [
        grade_threshold(single, config.THRESHOLDS["cinebench"]["single_core"]),
        grade_threshold(multi, config.THRESHOLDS["cinebench"]["multi_core"]),
    ]
    notes = []
    if completed.returncode != 0:
        notes.append(completed.stderr.strip() or "Cinebench returned a non-zero exit code.")
    if single is None or multi is None:
        notes.append("Could not parse one or more Cinebench scores.")
    return make_result(
        name,
        "CPU",
        worst_status(statuses),
        metrics={"single_core": single, "multi_core": multi, "result_path": str(result_path)},
        notes=notes,
        raw=(completed.stdout + completed.stderr)[-4000:],
        started_at=started_at,
    )

