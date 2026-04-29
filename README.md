# Gaming Laptop Checker

Windows QC benchmark launcher for gaming laptops. The project packages into a single `GamingLaptopChecker.exe` that opens a green-on-black MAS-style terminal menu, runs selected hardware checks, and produces self-contained HTML and JSON reports.

> This tool is for laptop quality checking and benchmarking only. It does not activate Windows or modify Windows licensing.

## One-Line PowerShell Run

Paste this one line into PowerShell on the laptop you want to test:

```powershell
irm https://raw.githubusercontent.com/sniperox/gaming-laptop-checker/main/bootstrap.bat -OutFile "$env:TEMP\glc.bat"; Start-Process "$env:TEMP\glc.bat" -Verb RunAs
```

The tested laptop does not need an IDE, Git, source ZIP extraction, a Python virtual environment, or `pip install`. The bootstrap downloads only the release EXE and launches it in a styled `cmd.exe` window.

## Features

- MAS-style dark terminal interface with numbered, single-key menu navigation
- Quick, full, thermal, GPU, storage, and system-info test modes
- Configurable PASS / WARN / FAIL thresholds in `config.py`
- Modular benchmark runners under `tests/`
- Tool downloader manifest for external benchmark utilities
- HWiNFO64 shared-memory thermal polling when available
- Self-contained HTML and JSON reports under `output/`
- Standalone Windows EXE build using PyInstaller

## Menu Modes

| Key | Mode | Purpose |
| --- | --- | --- |
| `1` | Quick Check | CPU, storage, SMART, battery, Cinebench when available |
| `2` | Full QC Suite | Full sequential QC workflow from the project spec |
| `3` | Thermal Only | HWiNFO + Prime95 + AIDA64 + FurMark path |
| `4` | GPU Benchmarks | GPU inventory, FurMark, 3DMark, Geekbench, Afterburner |
| `5` | Storage & Health | SMART, storage speed, HD Tune / chkdsk fallback |
| `6` | System Info | Non-stress inventory checks |
| `7` | View Last Report | Opens the latest HTML report |
| `8` | Update Tools | Re-downloads configured benchmark tools |
| `H` | Help | Shows test descriptions |
| `0` | Exit | Closes the app |

## Build The EXE

Build on your own Windows development machine:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1 -Clean
```

The output is:

```text
dist\GamingLaptopChecker.exe
```

Upload that file as a GitHub Release asset named exactly:

```text
GamingLaptopChecker.exe
```

## GitHub Release Flow

1. Create a public GitHub repository named `gaming-laptop-checker`.
2. Push the source to `main`.
3. Create a release or tag such as `v1.0.0`.
4. Upload `dist\GamingLaptopChecker.exe` to the release assets, or let the included GitHub Actions workflow build it on tag push.

Release download URL format:

```text
https://github.com/sniperox/gaming-laptop-checker/releases/latest/download/GamingLaptopChecker.exe
```

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Useful checks:

```powershell
.\.venv\Scripts\python.exe main.py --version
.\.venv\Scripts\python.exe main.py --smoke-report
```

## External Benchmark Tools

The app is production-safe by default: missing commercial or licensed tools are skipped and reported instead of crashing. Configure approved direct vendor URLs in `config.py` under `TOOL_MANIFEST`, or place installed executables under `tools/`.

Supported external tools include HWiNFO64, HWMonitor, MSI Afterburner, Prime95, Cinebench, AIDA64, OCCT, FurMark, 3DMark, Geekbench, PCMark 10, CrystalDiskMark, CrystalDiskInfo, and HD Tune.

## Reports

Every run writes timestamped reports:

```text
output/gaming_laptop_report_YYYYMMDD_HHMMSS.html
output/gaming_laptop_report_YYYYMMDD_HHMMSS.json
output/latest_report.html
output/latest_report.json
```

The HTML report includes system summary, overall verdict, per-test cards, thermal timeline, and recommendations.

## Repository Layout

```text
bootstrap.bat              One-line launcher target; downloads and runs the EXE
build_exe.ps1              Local Windows build script
GamingLaptopChecker.spec   PyInstaller spec
config.py                  Thresholds, paths, tool manifest
downloader.py              Tool download and verification logic
main.py                    MAS-style terminal UI and suite orchestration
report.py                  HTML / JSON report generation
templates/                 Report template
tests/                     Benchmark and inventory modules
```

## License

MIT. See [LICENSE](LICENSE).
