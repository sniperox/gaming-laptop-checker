from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path
from typing import Any

import requests
from rich.console import Console
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn

import config
from tests.common import find_tool


console = Console()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length") or 0)
        with Progress(
            TextColumn("[bold green]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(destination.name, total=total or None)
            with destination.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        handle.write(chunk)
                        progress.update(task, advance=len(chunk))


def _extract_zip(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(destination)


def _artifact_name(tool_name: str, url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix or ".download"
    return f"{tool_name}{suffix}"


def prepare_tool(tool_name: str, force: bool = False) -> dict[str, Any]:
    manifest = config.TOOL_MANIFEST[tool_name]
    existing = find_tool(tool_name)
    if existing and not force:
        return {
            "tool": tool_name,
            "display_name": manifest["display_name"],
            "status": "ready",
            "exe_path": str(existing),
            "notes": ["Existing executable found."],
        }

    url = manifest.get("url", "").strip()
    if not url:
        return {
            "tool": tool_name,
            "display_name": manifest["display_name"],
            "status": "not_configured",
            "exe_path": str(existing) if existing else None,
            "homepage": manifest.get("homepage"),
            "notes": [
                "Direct download URL is not configured. Add an approved vendor URL in config.TOOL_MANIFEST.",
            ],
        }

    tool_dir = config.TOOLS_DIR / tool_name
    if force and tool_dir.exists():
        shutil.rmtree(tool_dir)
    tool_dir.mkdir(parents=True, exist_ok=True)
    download_path = tool_dir / _artifact_name(tool_name, url)

    try:
        _download(url, download_path)
        if download_path.stat().st_size == 0:
            raise RuntimeError("Downloaded file is empty.")
        expected_hash = manifest.get("sha256")
        if expected_hash and _sha256(download_path).lower() != expected_hash.lower():
            raise RuntimeError("SHA256 hash mismatch.")
        if manifest.get("archive") == "zip" or download_path.suffix.lower() == ".zip":
            _extract_zip(download_path, tool_dir)
        exe_path = find_tool(tool_name)
        status = "ready" if exe_path else "downloaded"
        notes = ["Downloaded successfully."]
        if status != "ready":
            notes.append("Downloaded artifact did not expose a known executable pattern yet.")
        return {
            "tool": tool_name,
            "display_name": manifest["display_name"],
            "status": status,
            "exe_path": str(exe_path) if exe_path else None,
            "download_path": str(download_path),
            "notes": notes,
        }
    except Exception as exc:
        return {
            "tool": tool_name,
            "display_name": manifest["display_name"],
            "status": "download_failed",
            "exe_path": None,
            "notes": [str(exc)],
            "homepage": manifest.get("homepage"),
        }


def download_all(force: bool = False, tool_names: list[str] | None = None) -> dict[str, dict[str, Any]]:
    selected = tool_names or list(config.TOOL_MANIFEST)
    results: dict[str, dict[str, Any]] = {}
    for tool_name in selected:
        console.print(f"[green]Checking {config.TOOL_MANIFEST[tool_name]['display_name']}[/]")
        results[tool_name] = prepare_tool(tool_name, force=force)
    return results


def main() -> None:
    results = download_all(force=False)
    ready = sum(1 for item in results.values() if item["status"] == "ready")
    console.print(f"[bold green]{ready}/{len(results)} tools ready.[/]")
    for item in results.values():
        if item["status"] != "ready":
            console.print(f"[yellow]{item['display_name']}[/]: {item['status']} - {'; '.join(item['notes'])}")


if __name__ == "__main__":
    main()

