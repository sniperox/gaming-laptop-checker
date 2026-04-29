from __future__ import annotations

import config
from tests.common import ensure_list, grade_threshold, is_windows, make_result, now_iso, powershell_json, skipped, worst_status


def run() -> dict:
    name = "S.M.A.R.T. Health"
    started_at = now_iso()
    if not is_windows():
        return skipped(name, "Storage", "Storage health checks are available on Windows only.")
    notes = []
    try:
        disks = ensure_list(
            powershell_json(
                "Get-PhysicalDisk | Select-Object FriendlyName,SerialNumber,MediaType,BusType,HealthStatus,"
                "OperationalStatus,Size",
                timeout=45,
            )
        )
        smart = ensure_list(
            powershell_json(
                "Get-CimInstance -Namespace root\\wmi -ClassName MSStorageDriver_FailurePredictStatus | "
                "Select-Object InstanceName,PredictFailure,Reason",
                timeout=45,
            )
        )
        failures = [item for item in smart if item.get("PredictFailure")]
        unhealthy = [disk for disk in disks if str(disk.get("HealthStatus", "")).lower() not in ("healthy", "ok")]
        smart_errors = len(failures) + len(unhealthy)
        status = grade_threshold(smart_errors, config.THRESHOLDS["storage"]["smart_errors"])
        if failures:
            notes.append("One or more drives report SMART failure prediction.")
        if unhealthy:
            notes.append("One or more physical disks are not Healthy.")
        return make_result(
            name,
            "Storage",
            status,
            metrics={"smart_errors": smart_errors, "disks": disks, "failure_predict": smart},
            notes=notes,
            started_at=started_at,
        )
    except Exception as exc:
        return skipped(name, "Storage", f"Storage health information unavailable: {exc}")

