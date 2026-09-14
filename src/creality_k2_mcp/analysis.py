"""Read-only inspection for local G-code and 3MF files."""

from __future__ import annotations

import json
from pathlib import Path
import re
import zipfile
from typing import Any


PROJECT_SETTINGS_PATH = "Metadata/project_settings.config"

_GCODE_PATTERNS = {
    "estimated_time": re.compile(
        r";\s*(?:total\s+)?estimated\s+printing\s+time[^=:]*[=:]\s*(.+)", re.I
    ),
    "filament_weight_g": re.compile(
        r";\s*(?:total\s+)?filament\s+(?:weight|used)\s*\[g\]\s*[=:]\s*([\d.]+)", re.I
    ),
    "filament_length_m": re.compile(
        r";\s*(?:total\s+)?filament\s+length\s*\[?m\]?\s*[=:]\s*([\d.]+)", re.I
    ),
    "total_layers": re.compile(r";\s*total\s+layer\s+number\s*[=:]\s*(\d+)", re.I),
    "layer_height_mm": re.compile(r";\s*layer_height\s*[=:]\s*([\d.]+)", re.I),
}


def analyze_gcode(path: Path) -> dict[str, Any]:
    """Extract common slicer comments without changing the G-code file."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"G-code file was not found: {path}")

    lines = _read_gcode_edges(path)
    result: dict[str, Any] = {
        "file_name": path.name,
        "file_size_mb": round(path.stat().st_size / 1_000_000, 2),
    }
    for key, pattern in _GCODE_PATTERNS.items():
        value = _first_match(lines, pattern)
        if value is None:
            continue
        if key in {"filament_weight_g", "filament_length_m", "layer_height_mm"}:
            result[key] = float(value)
        elif key == "total_layers":
            result[key] = int(value)
        else:
            result[key] = value
    return result


def analyze_3mf(path: Path) -> dict[str, Any]:
    """Read the embedded Creality project settings from a 3MF archive."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"3MF file was not found: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            raw = archive.read(PROJECT_SETTINGS_PATH)
            thumbnail_paths = [
                member.filename
                for member in archive.infolist()
                if "thumbnail" in member.filename.lower()
            ]
    except KeyError as exc:
        raise ValueError("This 3MF does not contain Creality project settings.") from exc
    except zipfile.BadZipFile as exc:
        raise ValueError("The selected file is not a readable 3MF archive.") from exc

    settings = json.loads(raw.decode("utf-8"))
    if not isinstance(settings, dict):
        raise ValueError("3MF project settings must be a JSON object.")
    printer_model = str(settings.get("printer_model", ""))
    return {
        "file_name": path.name,
        "settings_count": len(settings),
        "settings": settings,
        "is_k2_project": "K2" in printer_model.upper(),
        "thumbnail_paths": thumbnail_paths,
    }


def _read_gcode_edges(path: Path, *, head_lines: int = 600, tail_bytes: int = 200_000) -> list[str]:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        head = [line.rstrip("\n") for _, line in zip(range(head_lines), handle)]
    with path.open("rb") as handle:
        handle.seek(max(0, path.stat().st_size - tail_bytes))
        tail = handle.read().decode("utf-8", "ignore").splitlines()
    return head + tail


def _first_match(lines: list[str], pattern: re.Pattern[str]) -> str | None:
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            return match.group(1).strip()
    return None
