from __future__ import annotations

import mmap
import os
import struct
import subprocess
import time
from pathlib import Path
from typing import Any

import config
from tests.common import find_tool, is_windows, make_result, now_iso, terminate_process


_MONITOR_PROCESSES: list[subprocess.Popen[Any]] = []
_LAST_SNAPSHOT: dict[str, Any] = {
    "cpu_temp_c": None,
    "gpu_temp_c": None,
    "cpu_clock_mhz": None,
    "gpu_clock_mhz": None,
    "source": "unavailable",
    "timestamp": None,
}


def _c_string(blob: bytes, offset: int, size: int) -> str:
    raw = blob[offset : offset + size].split(b"\x00", 1)[0]
    return raw.decode("utf-8", errors="ignore").strip()


def _read_hwinfo_blob() -> bytes | None:
    if not is_windows():
        return None
    for tag_name in ("Global\\HWiNFO_SENS_SM2", "HWiNFO_SENS_SM2"):
        for size in (8 * 1024 * 1024, 2 * 1024 * 1024, 512 * 1024):
            try:
                with mmap.mmap(-1, size, tagname=tag_name, access=mmap.ACCESS_READ) as mapping:
                    return mapping[:]
            except (OSError, ValueError):
                continue
    return None


def read_hwinfo_shared_memory() -> dict[str, Any] | None:
    blob = _read_hwinfo_blob()
    if not blob or len(blob) < 40:
        return None
    try:
        (
            _signature,
            _version,
            _revision,
            _poll_time,
            _sensor_offset,
            _sensor_size,
            _sensor_count,
            reading_offset,
            reading_size,
            reading_count,
        ) = struct.unpack_from("<IIIQIIIIII", blob, 0)
    except struct.error:
        return None

    cpu_temps: list[float] = []
    gpu_temps: list[float] = []
    cpu_clocks: list[float] = []
    gpu_clocks: list[float] = []

    for index in range(int(reading_count)):
        base = int(reading_offset) + index * int(reading_size)
        if base + 316 > len(blob):
            break
        try:
            label = _c_string(blob, base + 12, 128)
            user_label = _c_string(blob, base + 140, 128)
            unit = _c_string(blob, base + 268, 16)
            value = struct.unpack_from("<d", blob, base + 284)[0]
        except struct.error:
            continue
        name = f"{label} {user_label}".lower()
        if not (-1000 < value < 10000):
            continue
        if unit in ("°C", "C") or "temp" in name:
            if "gpu" in name:
                gpu_temps.append(value)
            elif "cpu" in name or "core" in name or "package" in name:
                cpu_temps.append(value)
        elif unit.lower() == "mhz" or "clock" in name:
            if "gpu" in name:
                gpu_clocks.append(value)
            elif "cpu" in name or "core" in name:
                cpu_clocks.append(value)

    if not any((cpu_temps, gpu_temps, cpu_clocks, gpu_clocks)):
        return None
    return {
        "cpu_temp_c": round(max(cpu_temps), 1) if cpu_temps else None,
        "gpu_temp_c": round(max(gpu_temps), 1) if gpu_temps else None,
        "cpu_clock_mhz": round(max(cpu_clocks), 1) if cpu_clocks else None,
        "gpu_clock_mhz": round(max(gpu_clocks), 1) if gpu_clocks else None,
        "source": "HWiNFO64 shared memory",
        "timestamp": time.time(),
    }


def snapshot() -> dict[str, Any]:
    global _LAST_SNAPSHOT
    current = read_hwinfo_shared_memory()
    if current:
        _LAST_SNAPSHOT = current
    else:
        _LAST_SNAPSHOT = {**_LAST_SNAPSHOT, "timestamp": time.time()}
    return dict(_LAST_SNAPSHOT)


def format_snapshot() -> str:
    snap = snapshot()
    cpu = f"{snap['cpu_temp_c']:.0f}°C" if isinstance(snap.get("cpu_temp_c"), (int, float)) else "--"
    gpu = f"{snap['gpu_temp_c']:.0f}°C" if isinstance(snap.get("gpu_temp_c"), (int, float)) else "--"
    throttle = snap.get("throttle_pct")
    throttle_text = f"{throttle:.0f}%" if isinstance(throttle, (int, float)) else "0%"
    return f"CPU: {cpu}    GPU: {gpu}    Throttle: {throttle_text}"


def start_monitors() -> dict:
    name = "Start Thermal Monitors"
    started_at = now_iso()
    notes: list[str] = []
    started: list[str] = []
    for tool_name, args in {
        "hwinfo64": ["/SensorsOnly", "/Minimized"],
        "hwmonitor": [],
        "afterburner": [],
    }.items():
        tool = find_tool(tool_name)
        if not tool:
            notes.append(f"{config.TOOL_MANIFEST[tool_name]['display_name']} not found.")
            continue
        try:
            proc = subprocess.Popen([str(tool), *args], cwd=str(Path(tool).parent))
            _MONITOR_PROCESSES.append(proc)
            started.append(str(tool))
        except OSError as exc:
            notes.append(f"Could not start {tool}: {exc}")
    status = config.STATUS_PASS if started else config.STATUS_SKIP
    if not started:
        notes.append("Thermal telemetry will be unavailable unless HWiNFO shared memory is already running.")
    return make_result(name, "Thermals", status, metrics={"started": started}, notes=notes, started_at=started_at)


def stop_monitors() -> dict:
    name = "Stop Thermal Monitors"
    started_at = now_iso()
    stopped = 0
    while _MONITOR_PROCESSES:
        proc = _MONITOR_PROCESSES.pop()
        if proc.poll() is None:
            terminate_process(proc)
            stopped += 1
    return make_result(name, "Thermals", config.STATUS_PASS, metrics={"stopped": stopped}, started_at=started_at)


def run_idle_sample(seconds: int = 10) -> dict:
    name = "Thermal Idle Sample"
    started_at = now_iso()
    samples = []
    deadline = time.time() + seconds
    while time.time() < deadline:
        samples.append(snapshot())
        time.sleep(min(config.TEST_DURATIONS_SECONDS["thermal_poll"], max(0.2, deadline - time.time())))
    cpu_values = [item["cpu_temp_c"] for item in samples if isinstance(item.get("cpu_temp_c"), (int, float))]
    gpu_values = [item["gpu_temp_c"] for item in samples if isinstance(item.get("gpu_temp_c"), (int, float))]
    status = config.STATUS_PASS if cpu_values or gpu_values else config.STATUS_SKIP
    return make_result(
        name,
        "Thermals",
        status,
        metrics={
            "cpu_idle_temp_c": round(sum(cpu_values) / len(cpu_values), 1) if cpu_values else None,
            "gpu_idle_temp_c": round(sum(gpu_values) / len(gpu_values), 1) if gpu_values else None,
            "thermal_samples": samples,
        },
        notes=[] if status == config.STATUS_PASS else ["No thermal samples were available."],
        started_at=started_at,
    )

