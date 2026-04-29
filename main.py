from __future__ import annotations

import os
import sys
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, ProgressColumn, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text

import config
import downloader
import report
from tests import (
    afterburner,
    aida64,
    battery,
    cinebench,
    cpu_info,
    display,
    furmark,
    geekbench,
    gpu_info,
    hdtune,
    hwmonitor,
    network,
    occt,
    pcmark10,
    prime95,
    ram,
    storage_health,
    storage_speed,
    thermals,
    threedmark,
)
from tests.common import make_result, now_iso, os_summary, windows_admin_status

try:
    import msvcrt
except ImportError:  # pragma: no cover - Windows-only UX
    msvcrt = None


console = Console()


@dataclass(frozen=True)
class Step:
    name: str
    runner: Callable[[], dict]


class ThermalColumn(ProgressColumn):
    def render(self, task):  # type: ignore[override]
        return Text(thermals.format_snapshot(), style="bright_green")


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def get_single_key(valid: set[str] | None = None) -> str:
    if msvcrt and os.name == "nt":
        while True:
            key = msvcrt.getch()
            try:
                value = key.decode("utf-8").upper()
            except UnicodeDecodeError:
                continue
            if valid is None or value in valid:
                return value
    while True:
        value = input().strip().upper()[:1]
        if valid is None or value in valid:
            return value


def build_menu_text() -> Text:
    line = "─" * 65
    text = Text()
    text.append(f"{line}\n", style="#00FF41")
    text.append("         Gaming Laptop Checker  v1.0\n", style="bold #00FF41")
    text.append("         Automated QC Benchmark System\n", style="white")
    text.append(f"{line}\n", style="#00FF41")
    text.append("  Test Modes:\n", style="bold white")
    text.append("  [1] Quick Check          ", style="bold #00FF41")
    text.append("- Cinebench + Storage + Battery   (~15 min)\n", style="white")
    text.append("  [2] Full QC Suite        ", style="bold #00FF41")
    text.append("- All tests sequential             (~75 min)\n", style="white")
    text.append("  [3] Thermal Only         ", style="bold #00FF41")
    text.append("- Prime95 + AIDA64 + FurMark       (~35 min)\n", style="white")
    text.append("  [4] GPU Benchmarks       ", style="bold #00FF41")
    text.append("- 3DMark + FurMark + Geekbench GPU (~30 min)\n", style="white")
    text.append("  [5] Storage & Health     ", style="bold #00FF41")
    text.append("- CDM + CDI + HD Tune              (~12 min)\n", style="white")
    text.append(f"{line}\n", style="#00FF41")
    text.append("  [6] Check System Info    - CPU / GPU / RAM / Storage (no tests)\n", style="white")
    text.append("  [7] View Last Report     - Open previous HTML report in browser\n", style="white")
    text.append("  [8] Update Tools         - Re-download all benchmark tools\n", style="white")
    text.append("  [H] Help                 - Show test descriptions\n", style="white")
    text.append("  [0] Exit\n", style="white")
    text.append(f"{line}\n", style="#00FF41")
    text.append("  Choose a menu option using your keyboard [1,2...H,0] : ", style="bold white")
    return text


def show_menu() -> str:
    clear_screen()
    console.print(
        Panel(
            build_menu_text(),
            title="[bold #00FF41]Gaming Laptop Checker v1.0[/]",
            border_style="#00FF41",
            expand=False,
        )
    )
    return get_single_key(set("12345678H0"))


def run_admin_check() -> dict:
    started_at = now_iso()
    is_admin, label = windows_admin_status()
    metrics = {"admin": is_admin, "admin_label": label, "os": os_summary()}
    status = config.STATUS_PASS if is_admin else config.STATUS_WARN
    notes = [] if is_admin else ["Administrator mode is recommended for complete hardware telemetry and stress tests."]
    return make_result("OS / Admin Check", "System", status, metrics=metrics, notes=notes, started_at=started_at)


def run_downloader(force: bool = False, tool_names: list[str] | None = None) -> dict:
    started_at = now_iso()
    results = downloader.download_all(force=force, tool_names=tool_names)
    ready = sum(1 for item in results.values() if item.get("status") == "ready")
    configured_missing = [item["display_name"] for item in results.values() if item.get("status") == "not_configured"]
    failed = [item["display_name"] for item in results.values() if item.get("status") == "download_failed"]
    status = config.STATUS_PASS
    notes = []
    if configured_missing:
        status = config.STATUS_WARN
        notes.append("Direct URLs not configured for: " + ", ".join(configured_missing))
    if failed:
        status = config.STATUS_WARN
        notes.append("Downloads failed for: " + ", ".join(failed))
    return make_result(
        "Tool Downloader",
        "Setup",
        status,
        metrics={"ready": ready, "total": len(results), "tools": results},
        notes=notes,
        started_at=started_at,
    )


def quick_steps() -> list[Step]:
    return [
        Step("OS / Admin Check", run_admin_check),
        Step("Download Missing Tools", lambda: run_downloader(tool_names=["cinebench", "crystaldiskmark", "crystaldiskinfo"])),
        Step("CPU Info", cpu_info.run),
        Step("Storage Speed", storage_speed.run),
        Step("S.M.A.R.T. Health", storage_health.run),
        Step("Battery Health", battery.run),
        Step("Cinebench R23", cinebench.run),
    ]


def full_steps() -> list[Step]:
    return [
        Step("OS / Admin Check", run_admin_check),
        Step("Download Missing Tools", lambda: run_downloader(force=False)),
        Step("Start Thermal Monitors", thermals.start_monitors),
        Step("CPU Info", cpu_info.run),
        Step("GPU Info", gpu_info.run),
        Step("RAM", ram.run),
        Step("Battery Health", battery.run),
        Step("Display", display.run),
        Step("Wi-Fi Speed", network.run),
        Step("S.M.A.R.T. Health", storage_health.run),
        Step("Storage Speed", storage_speed.run),
        Step("HD Tune Error Scan", hdtune.run),
        Step("Cinebench R23", cinebench.run),
        Step("OCCT CPU", occt.run_cpu),
        Step("OCCT GPU", occt.run_gpu),
        Step("Prime95 Small FFTs", prime95.run),
        Step("AIDA64 Stability", aida64.run),
        Step("FurMark GPU Torture", furmark.run),
        Step("3DMark", threedmark.run),
        Step("Geekbench 6", geekbench.run),
        Step("PCMark 10", pcmark10.run),
        Step("HWMonitor", hwmonitor.run),
        Step("MSI Afterburner", afterburner.run),
        Step("Stop Thermal Monitors", thermals.stop_monitors),
    ]


def thermal_steps() -> list[Step]:
    return [
        Step("OS / Admin Check", run_admin_check),
        Step("Download Thermal Tools", lambda: run_downloader(tool_names=["hwinfo64", "prime95", "aida64", "furmark"])),
        Step("Start Thermal Monitors", thermals.start_monitors),
        Step("Thermal Idle Sample", thermals.run_idle_sample),
        Step("Prime95 Small FFTs", prime95.run),
        Step("AIDA64 Stability", aida64.run),
        Step("FurMark GPU Torture", furmark.run),
        Step("Stop Thermal Monitors", thermals.stop_monitors),
    ]


def gpu_steps() -> list[Step]:
    return [
        Step("OS / Admin Check", run_admin_check),
        Step("Download GPU Tools", lambda: run_downloader(tool_names=["hwinfo64", "furmark", "3dmark", "geekbench", "afterburner"])),
        Step("Start Thermal Monitors", thermals.start_monitors),
        Step("GPU Info", gpu_info.run),
        Step("FurMark GPU Torture", furmark.run),
        Step("3DMark", threedmark.run),
        Step("Geekbench 6", geekbench.run),
        Step("MSI Afterburner", afterburner.run),
        Step("Stop Thermal Monitors", thermals.stop_monitors),
    ]


def storage_steps() -> list[Step]:
    return [
        Step("OS / Admin Check", run_admin_check),
        Step("Download Storage Tools", lambda: run_downloader(tool_names=["crystaldiskmark", "crystaldiskinfo", "hdtune"])),
        Step("S.M.A.R.T. Health", storage_health.run),
        Step("Storage Speed", storage_speed.run),
        Step("HD Tune Error Scan", hdtune.run),
    ]


def info_steps() -> list[Step]:
    return [
        Step("OS / Admin Check", run_admin_check),
        Step("CPU Info", cpu_info.run),
        Step("GPU Info", gpu_info.run),
        Step("RAM", ram.run),
        Step("Battery Health", battery.run),
        Step("Display", display.run),
        Step("S.M.A.R.T. Health", storage_health.run),
    ]


SUITES: dict[str, tuple[str, Callable[[], list[Step]]]] = {
    "1": ("Quick Check", quick_steps),
    "2": ("Full QC Suite", full_steps),
    "3": ("Thermal Only", thermal_steps),
    "4": ("GPU Benchmarks", gpu_steps),
    "5": ("Storage & Health", storage_steps),
    "6": ("System Info", info_steps),
}


def status_style(status: str) -> str:
    return {
        config.STATUS_PASS: "green",
        config.STATUS_WARN: "yellow",
        config.STATUS_FAIL: "red",
        config.STATUS_SKIP: "white",
    }.get(status, "white")


def run_suite(choice: str) -> None:
    suite_name, builder = SUITES[choice]
    steps = builder()
    results: list[dict] = []
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    clear_screen()
    console.print(Panel(f"[bold #00FF41]{suite_name}[/]\nTests run sequentially. Failures are recorded and the suite continues.", border_style="#00FF41"))
    time.sleep(0.6)
    with Progress(
        SpinnerColumn(style="#00FF41"),
        TextColumn("{task.description}"),
        BarColumn(bar_width=24),
        TextColumn("{task.fields[badge]}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        ThermalColumn(),
        console=console,
        refresh_per_second=2,
    ) as progress:
        for index, step in enumerate(steps, start=1):
            description = f"[{index}/{len(steps)}] {step.name}"
            task = progress.add_task(description, total=1, badge="[cyan]Running[/]")
            try:
                result = step.runner()
            except KeyboardInterrupt:
                thermals.stop_monitors()
                raise
            except Exception as exc:
                result = make_result(step.name, "Internal", config.STATUS_FAIL, notes=[f"Unhandled error: {exc}"])
            results.append(result)
            badge = f"[{status_style(result['status'])}][{result['status']}][/]"
            progress.update(task, completed=1, badge=badge)

    finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
    report_paths = report.generate_report(results, suite_name=suite_name, started_at=started_at, finished_at=finished_at)
    show_summary(results, report_paths)


def show_summary(results: list[dict], report_paths: dict[str, str]) -> None:
    table = Table(title="Gaming Laptop Checker Summary", border_style="#00FF41")
    table.add_column("Test")
    table.add_column("Category")
    table.add_column("Status")
    table.add_column("Notes")
    for item in results:
        table.add_row(
            item.get("name", ""),
            item.get("category", ""),
            f"[{status_style(item.get('status'))}]{item.get('status')}[/]",
            "; ".join(item.get("notes") or [])[:90],
        )
    console.print(table)
    console.print(f"[green]HTML report:[/] {report_paths['html_path']}")
    console.print(f"[green]JSON report:[/] {report_paths['json_path']}")
    console.print("[bold white]Open report in browser? [Y/N][/]")
    if get_single_key(set("YN")) == "Y":
        webbrowser.open(Path(report_paths["html_path"]).resolve().as_uri())


def open_last_report() -> None:
    path = config.OUTPUT_DIR / "latest_report.html"
    if path.exists():
        webbrowser.open(path.resolve().as_uri())
        console.print(f"[green]Opened:[/] {path}")
    else:
        console.print("[yellow]No report found yet. Run a suite first.[/]")
    console.print("Press any key to continue.")
    get_single_key()


def update_tools() -> None:
    clear_screen()
    result = run_downloader(force=True)
    console.print(Panel(f"Tools ready: {result['metrics']['ready']}/{result['metrics']['total']}", title="Tool Update", border_style="#00FF41"))
    for tool_name, item in result["metrics"]["tools"].items():
        style = "green" if item["status"] == "ready" else "yellow"
        console.print(f"[{style}]{item['display_name']}[/] - {item['status']} - {'; '.join(item['notes'])}")
    console.print("Press any key to continue.")
    get_single_key()


def show_help() -> None:
    clear_screen()
    help_text = """
[bold #00FF41]Test descriptions[/]

[green]Quick Check[/] runs CPU info, storage speed, SMART health, battery health, and Cinebench when available.
[green]Full QC Suite[/] follows the DOCX order: setup, monitoring, system inventory, battery/display/network, storage, CPU, GPU, and productivity benchmarks.
[green]Thermal Only[/] starts monitors, samples idle temperatures, then runs Prime95, AIDA64, and FurMark.
[green]GPU Benchmarks[/] focuses on GPU info, FurMark, 3DMark, Geekbench, and Afterburner logging.
[green]Storage & Health[/] runs SMART health, WinSAT/CrystalDiskMark speed, and HD Tune/chkdsk scan.

External commercial tools are skipped until their approved download URLs or installed executables are present in tools/.
"""
    console.print(Panel(help_text.strip(), title="Help", border_style="#00FF41"))
    console.print("Press any key to continue.")
    get_single_key()


def main() -> int:
    if "--version" in sys.argv:
        print(f"{config.APP_TITLE} {config.APP_VERSION}")
        return 0
    if "--smoke-report" in sys.argv:
        started = now_iso()
        result = make_result("Packaged EXE Smoke Test", "Internal", config.STATUS_PASS, metrics={"frozen": getattr(sys, "frozen", False)}, started_at=started)
        paths = report.generate_report([result], suite_name="Packaged Smoke Test", started_at=started)
        print(paths["html_path"])
        print(paths["json_path"])
        return 0
    if os.name == "nt":
        os.system("title Gaming Laptop Checker")
    while True:
        choice = show_menu()
        if choice in SUITES:
            run_suite(choice)
            console.print("Press any key to return to the menu.")
            get_single_key()
        elif choice == "7":
            open_last_report()
        elif choice == "8":
            update_tools()
        elif choice == "H":
            show_help()
        elif choice == "0":
            clear_screen()
            console.print("[green]Exiting Gaming Laptop Checker.[/]")
            return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        thermals.stop_monitors()
        console.print("\n[red]Interrupted. Thermal monitor processes were stopped.[/]")
        raise SystemExit(130)
