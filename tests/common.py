from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import config


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def is_windows() -> bool:
    return os.name == "nt"


def make_result(
    name: str,
    category: str,
    status: str,
    metrics: dict[str, Any] | None = None,
    notes: list[str] | None = None,
    raw: Any | None = None,
    started_at: str | None = None,
) -> dict[str, Any]:
    finished_at = now_iso()
    duration = None
    if started_at:
        try:
            duration = (
                datetime.fromisoformat(finished_at)
                - datetime.fromisoformat(started_at)
            ).total_seconds()
        except ValueError:
            duration = None
    return {
        "name": name,
        "category": category,
        "status": status,
        "metrics": metrics or {},
        "notes": notes or [],
        "raw": raw,
        "started_at": started_at or finished_at,
        "finished_at": finished_at,
        "duration_seconds": duration,
    }


def skipped(name: str, category: str, reason: str, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    return make_result(name, category, config.STATUS_SKIP, metrics=metrics, notes=[reason])


def failed(name: str, category: str, reason: str, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    return make_result(name, category, config.STATUS_FAIL, metrics=metrics, notes=[reason])


def run_command(
    command: list[str] | str,
    timeout: int = 60,
    cwd: Path | str | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        shell=isinstance(command, str),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=check,
    )


def run_powershell(script: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return run_command(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        timeout=timeout,
    )


def powershell_json(script: str, timeout: int = 60) -> Any:
    completed = run_powershell(f"{script} | ConvertTo-Json -Depth 6", timeout=timeout)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    output = completed.stdout.strip()
    if not output:
        return None
    return json.loads(output)


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def as_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def grade_min(value: Any, pass_min: float, warn_min: float) -> str:
    numeric = as_number(value)
    if numeric is None:
        return config.STATUS_SKIP
    if numeric >= pass_min:
        return config.STATUS_PASS
    if numeric >= warn_min:
        return config.STATUS_WARN
    return config.STATUS_FAIL


def grade_max(value: Any, pass_max: float, warn_max: float) -> str:
    numeric = as_number(value)
    if numeric is None:
        return config.STATUS_SKIP
    if numeric <= pass_max:
        return config.STATUS_PASS
    if numeric <= warn_max:
        return config.STATUS_WARN
    return config.STATUS_FAIL


def grade_threshold(value: Any, threshold: dict[str, float]) -> str:
    if "pass_min" in threshold:
        return grade_min(value, threshold["pass_min"], threshold["warn_min"])
    return grade_max(value, threshold["pass_max"], threshold["warn_max"])


def worst_status(statuses: Iterable[str]) -> str:
    order = {
        config.STATUS_FAIL: 3,
        config.STATUS_WARN: 2,
        config.STATUS_SKIP: 1,
        config.STATUS_PASS: 0,
    }
    items = list(statuses)
    if not items:
        return config.STATUS_SKIP
    return max(items, key=lambda status: order.get(status, 1))


def find_tool(tool_name: str) -> Path | None:
    manifest = config.TOOL_MANIFEST.get(tool_name, {})
    patterns = manifest.get("exe_patterns", [])
    for root in config.TOOL_SEARCH_PATHS:
        if not root.exists():
            continue
        for pattern in patterns:
            direct = root / tool_name / pattern
            if direct.exists():
                return direct
        try:
            for pattern in patterns:
                matches = list(root.rglob(pattern))
                if matches:
                    return matches[0]
        except (OSError, PermissionError):
            continue
    for pattern in patterns:
        found = shutil.which(pattern)
        if found:
            return Path(found)
    return None


def parse_key_value_output(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def safe_unlink(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def terminate_process(proc: subprocess.Popen[Any], grace_seconds: int = 5) -> None:
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        deadline = time.time() + grace_seconds
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.2)
        if proc.poll() is None:
            proc.kill()
    except OSError:
        pass


def windows_admin_status() -> tuple[bool, str]:
    if not is_windows():
        return False, "Not running on Windows"
    try:
        import ctypes

        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        return is_admin, "Administrator" if is_admin else "Standard user"
    except Exception as exc:  # pragma: no cover - Windows API only
        return False, f"Unable to query admin status: {exc}"


def os_summary() -> dict[str, Any]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
    }

