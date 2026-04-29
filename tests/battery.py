from __future__ import annotations

import xml.etree.ElementTree as ET

import config
from tests.common import grade_threshold, is_windows, make_result, now_iso, powershell_json, run_command, skipped


def _xml_text(root: ET.Element, wanted: str) -> str | None:
    for element in root.iter():
        if element.tag.lower().endswith(wanted.lower()) and element.text:
            return element.text.strip()
    return None


def _number(text: str | None) -> float | None:
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
    return float(digits) if digits else None


def run() -> dict:
    name = "Battery Health"
    started_at = now_iso()
    if not is_windows():
        return skipped(name, "Battery", "Battery report is available on Windows only.")
    report_xml = config.OUTPUT_DIR / "battery-report.xml"
    notes = []
    metrics = {}
    try:
        completed = run_command(
            ["powercfg", "/batteryreport", "/xml", "/output", str(report_xml)],
            timeout=60,
        )
        if completed.returncode == 0 and report_xml.exists():
            root = ET.parse(report_xml).getroot()
            design = _number(_xml_text(root, "DesignCapacity"))
            full = _number(_xml_text(root, "FullChargeCapacity"))
            cycle_count = _number(_xml_text(root, "CycleCount"))
            capacity_pct = round(full / design * 100, 2) if design and full else None
            metrics.update(
                {
                    "design_capacity_mwh": design,
                    "full_charge_capacity_mwh": full,
                    "capacity_pct": capacity_pct,
                    "cycle_count": cycle_count,
                    "report_path": str(report_xml),
                }
            )
        else:
            notes.append(completed.stderr.strip() or completed.stdout.strip() or "powercfg battery report failed.")
        if not metrics.get("capacity_pct"):
            data = powershell_json(
                "Get-CimInstance Win32_Battery | Select-Object Name,BatteryStatus,EstimatedChargeRemaining,EstimatedRunTime",
                timeout=30,
            )
            metrics["wmi"] = data
            notes.append("Full charge capacity was unavailable; WMI battery status captured instead.")
        status = grade_threshold(metrics.get("capacity_pct"), config.THRESHOLDS["battery"]["capacity_pct"])
        return make_result(name, "Battery", status, metrics=metrics, notes=notes, started_at=started_at)
    except Exception as exc:
        return skipped(name, "Battery", f"Battery information unavailable: {exc}", metrics=metrics)

