from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_NAME = "gaming-laptop-checker"
APP_TITLE = "Gaming Laptop Checker"
APP_VERSION = "1.0"

if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", ROOT_DIR))
else:
    ROOT_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = ROOT_DIR

TOOLS_DIR = ROOT_DIR / "tools"
OUTPUT_DIR = ROOT_DIR / "output"
TEMPLATE_DIR = RESOURCE_DIR / "templates"

TOOLS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_SKIP = "SKIP"

STATUS_COLORS = {
    STATUS_PASS: "#16A34A",
    STATUS_WARN: "#D97706",
    STATUS_FAIL: "#DC2626",
    STATUS_SKIP: "#6B7280",
}

# Set GLC_FAST_MODE=1 when developing the UI only. Production runs use the
# durations from the project specification.
FAST_MODE = os.getenv("GLC_FAST_MODE", "").strip() == "1"

TEST_DURATIONS_SECONDS = {
    "prime95": 30 if FAST_MODE else 10 * 60,
    "aida64": 30 if FAST_MODE else 15 * 60,
    "furmark": 30 if FAST_MODE else 10 * 60,
    "occt_cpu": 20 if FAST_MODE else 5 * 60,
    "occt_gpu": 20 if FAST_MODE else 5 * 60,
    "occt_memory": 20 if FAST_MODE else 5 * 60,
    "thermal_poll": 5,
}

THRESHOLDS = {
    "cinebench": {
        "multi_core": {"pass_min": 15000, "warn_min": 10000},
        "single_core": {"pass_min": 1800, "warn_min": 1400},
    },
    "prime95": {
        "throttle_pct": {"pass_max": 5, "warn_max": 15},
        "cpu_temp_c": {"pass_max": 90, "warn_max": 95},
    },
    "aida64": {
        "cpu_temp_c": {"pass_max": 90, "warn_max": 95},
    },
    "occt": {
        "errors": {"pass_max": 0, "warn_max": 0},
    },
    "furmark": {
        "gpu_temp_c": {"pass_max": 85, "warn_max": 92},
    },
    "3dmark": {
        "fire_strike": {"pass_min": 13000, "warn_min": 10000},
        "time_spy": {"pass_min": 6500, "warn_min": 5000},
        "port_royal": {"pass_min": 3000, "warn_min": 2000},
        "night_raid": {"pass_min": 35000, "warn_min": 25000},
        "speed_way": {"pass_min": 1400, "warn_min": 1000},
    },
    "geekbench": {
        "single_core": {"pass_min": 2200, "warn_min": 1800},
        "multi_core": {"pass_min": 12000, "warn_min": 9000},
    },
    "pcmark10": {
        "score": {"pass_min": 7000, "warn_min": 5000},
    },
    "storage": {
        "seq_read_mbps": {"pass_min": 3000, "warn_min": 1500},
        "random_4k_read_mbps": {"pass_min": 60, "warn_min": 30},
        "smart_errors": {"pass_max": 0, "warn_max": 0},
    },
    "battery": {
        "capacity_pct": {"pass_min": 80, "warn_min": 60},
    },
    "ram": {
        "speed_mhz": {"pass_min": 3200, "warn_min": 2666},
    },
    "network": {
        "download_mbps": {"pass_min": 200, "warn_min": 50},
    },
}

# External tools are intentionally manifest-driven. A few vendors change their
# direct URLs frequently or require license acceptance/activation, so leave
# empty URLs for those tools until you publish your own approved mirrors.
TOOL_MANIFEST = {
    "hwinfo64": {
        "display_name": "HWiNFO64",
        "url": "",
        "homepage": "https://www.hwinfo.com/download/",
        "exe_patterns": ["HWiNFO64.exe"],
        "archive": "zip",
        "required_for": ["thermal telemetry"],
    },
    "hwmonitor": {
        "display_name": "HWMonitor",
        "url": "",
        "homepage": "https://www.cpuid.com/softwares/hwmonitor.html",
        "exe_patterns": ["HWMonitor.exe", "HWMonitor_x64.exe"],
        "archive": "zip",
        "required_for": ["fan and voltage telemetry"],
    },
    "afterburner": {
        "display_name": "MSI Afterburner",
        "url": "",
        "homepage": "https://www.msi.com/Landing/afterburner/graphics-cards",
        "exe_patterns": ["MSIAfterburner.exe"],
        "archive": "installer",
        "required_for": ["GPU clock logging"],
    },
    "prime95": {
        "display_name": "Prime95",
        "url": "https://www.mersenne.org/ftp_root/gimps/p95v308b17.win64.zip",
        "homepage": "https://www.mersenne.org/download/",
        "exe_patterns": ["prime95.exe"],
        "archive": "zip",
        "required_for": ["CPU thermal stress"],
    },
    "cinebench": {
        "display_name": "Cinebench R23",
        "url": "",
        "homepage": "https://www.maxon.net/en/downloads/cinebench-2024-downloads",
        "exe_patterns": ["Cinebench.exe", "CinebenchR23.exe"],
        "archive": "zip",
        "required_for": ["CPU benchmark"],
    },
    "aida64": {
        "display_name": "AIDA64 Extreme",
        "url": "",
        "homepage": "https://www.aida64.com/downloads",
        "exe_patterns": ["aida64.exe"],
        "archive": "zip",
        "required_for": ["stability test"],
    },
    "occt": {
        "display_name": "OCCT",
        "url": "",
        "homepage": "https://www.ocbase.com/download",
        "exe_patterns": ["OCCT.exe", "occt.exe"],
        "archive": "installer",
        "required_for": ["CPU/GPU error detection"],
    },
    "furmark": {
        "display_name": "FurMark",
        "url": "",
        "homepage": "https://geeks3d.com/furmark/downloads/",
        "exe_patterns": ["FurMark.exe", "FurMark_GUI.exe"],
        "archive": "installer",
        "required_for": ["GPU stress test"],
    },
    "3dmark": {
        "display_name": "3DMark",
        "url": "",
        "homepage": "https://benchmarks.ul.com/3dmark",
        "exe_patterns": ["3DMarkCmd.exe", "3DMark.exe"],
        "archive": "installer",
        "required_for": ["GPU benchmarks"],
    },
    "geekbench": {
        "display_name": "Geekbench 6",
        "url": "",
        "homepage": "https://www.geekbench.com/download/windows/",
        "exe_patterns": ["geekbench6.exe", "Geekbench 6.exe"],
        "archive": "installer",
        "required_for": ["CPU/GPU compute benchmark"],
    },
    "pcmark10": {
        "display_name": "PCMark 10",
        "url": "",
        "homepage": "https://benchmarks.ul.com/pcmark10",
        "exe_patterns": ["PCMark10Cmd.exe", "PCMark10.exe"],
        "archive": "installer",
        "required_for": ["productivity benchmark"],
    },
    "crystaldiskmark": {
        "display_name": "CrystalDiskMark",
        "url": "",
        "homepage": "https://crystalmark.info/en/software/crystaldiskmark/",
        "exe_patterns": ["DiskMark64.exe", "DiskMark32.exe", "CrystalDiskMark.exe"],
        "archive": "zip",
        "required_for": ["storage speed"],
    },
    "crystaldiskinfo": {
        "display_name": "CrystalDiskInfo",
        "url": "",
        "homepage": "https://crystalmark.info/en/software/crystaldiskinfo/",
        "exe_patterns": ["DiskInfo64.exe", "DiskInfo32.exe", "CrystalDiskInfo.exe"],
        "archive": "zip",
        "required_for": ["SMART health"],
    },
    "hdtune": {
        "display_name": "HD Tune",
        "url": "",
        "homepage": "https://www.hdtune.com/download.html",
        "exe_patterns": ["HDTune.exe", "HDTunePro.exe"],
        "archive": "installer",
        "required_for": ["drive error scan"],
    },
}

TOOL_SEARCH_PATHS = [
    TOOLS_DIR,
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
]
