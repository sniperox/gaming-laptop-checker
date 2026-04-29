from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

import config


def _overall_status(results: list[dict[str, Any]]) -> str:
    statuses = [item.get("status") for item in results]
    if config.STATUS_FAIL in statuses:
        return "FAIL"
    if config.STATUS_WARN in statuses:
        return "NEEDS ATTENTION"
    if statuses and all(status == config.STATUS_SKIP for status in statuses):
        return "SKIP"
    return "PASS"


def _system_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for result in results:
        metrics = result.get("metrics", {})
        if result.get("name") == "CPU Info":
            summary["CPU"] = metrics.get("model")
        elif result.get("name") == "GPU Info":
            gpus = metrics.get("gpus") or []
            summary["GPU"] = ", ".join(gpu.get("name", "") for gpu in gpus if gpu.get("name"))
        elif result.get("name") == "RAM":
            total = metrics.get("total_gb")
            speed = metrics.get("effective_speed_mhz")
            summary["RAM"] = f"{total} GB @ {speed} MHz" if total else None
        elif result.get("name") == "Storage Speed":
            summary["Storage Seq Read"] = metrics.get("seq_read_mbps")
        elif result.get("name") == "OS / Admin Check":
            summary["OS"] = metrics.get("os", {}).get("version") or metrics.get("os", {}).get("release")
            summary["Admin"] = metrics.get("admin_label")
    return {key: value for key, value in summary.items() if value not in (None, "")}


def _recommendations(results: list[dict[str, Any]]) -> list[str]:
    recommendations = []
    for result in results:
        if result.get("status") in (config.STATUS_WARN, config.STATUS_FAIL):
            name = result.get("name")
            notes = "; ".join(result.get("notes") or [])
            if notes:
                recommendations.append(f"{name}: {notes}")
            else:
                recommendations.append(f"{name}: review measured values against thresholds.")
    return recommendations


def _thermal_series(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    series = []
    index = 0
    for result in results:
        for sample in result.get("metrics", {}).get("thermal_samples", []) or []:
            series.append(
                {
                    "index": index,
                    "label": result.get("name"),
                    "cpu": sample.get("cpu_temp_c"),
                    "gpu": sample.get("gpu_temp_c"),
                    "cpu_clock": sample.get("cpu_clock_mhz"),
                    "gpu_clock": sample.get("gpu_clock_mhz"),
                }
            )
            index += 1
    return series


def generate_report(
    results: list[dict[str, Any]],
    suite_name: str,
    started_at: str,
    finished_at: str | None = None,
) -> dict[str, str]:
    finished_at = finished_at or datetime.now().astimezone().isoformat(timespec="seconds")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"gaming_laptop_report_{timestamp}"
    json_path = config.OUTPUT_DIR / f"{base_name}.json"
    html_path = config.OUTPUT_DIR / f"{base_name}.html"

    payload = {
        "project": config.PROJECT_NAME,
        "app_version": config.APP_VERSION,
        "suite_name": suite_name,
        "started_at": started_at,
        "finished_at": finished_at,
        "overall_status": _overall_status(results),
        "system_summary": _system_summary(results),
        "recommendations": _recommendations(results),
        "thermal_series": _thermal_series(results),
        "results": results,
        "status_colors": config.STATUS_COLORS,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    env = Environment(
        loader=FileSystemLoader(str(config.TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")
    html = template.render(payload=payload, payload_json=json.dumps(payload, ensure_ascii=False))
    html_path.write_text(html, encoding="utf-8")

    latest_html = config.OUTPUT_DIR / "latest_report.html"
    latest_json = config.OUTPUT_DIR / "latest_report.json"
    shutil.copyfile(html_path, latest_html)
    shutil.copyfile(json_path, latest_json)

    return {
        "html_path": str(html_path),
        "json_path": str(json_path),
        "latest_html": str(latest_html),
        "latest_json": str(latest_json),
    }

