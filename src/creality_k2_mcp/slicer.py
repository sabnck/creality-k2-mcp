"""Validated local profile discovery and Creality Print command planning."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import re
from typing import Any

from .config import Settings


_K2_NOZZLE = re.compile(r"(?:^|@)Creality K2\s+(\d\.\d)\s+nozzle$", re.I)


class ProfileCatalog:
    """Discover only the profiles installed on the current computer."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def list_for_nozzle(self, nozzle: str) -> dict[str, dict[str, Path]]:
        catalog = {kind: self._profiles(kind, nozzle) for kind in ("machine", "process", "filament")}
        if not catalog["process"]:
            raise ValueError(f"No profiles were found for nozzle {nozzle}.")
        return catalog

    def _profiles(self, kind: str, nozzle: str) -> dict[str, Path]:
        directory = self.root / kind
        if not directory.is_dir():
            return {}
        found: dict[str, Path] = {}
        for profile in directory.glob("*.json"):
            match = _K2_NOZZLE.search(profile.stem)
            if match and match.group(1) == nozzle:
                found[profile.stem] = profile
        return found


class SlicePlanner:
    """Build a slice command after validating local profiles and overrides.

    This class does not invoke the slicer. The MCP layer can decide whether to
    launch a planned command in a user-owned working directory.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def prepare(
        self,
        *,
        model: Path,
        nozzle: str,
        material: str,
        process: str,
        overrides: Mapping[str, Any] | None,
        output_dir: Path,
    ) -> dict[str, Any]:
        model = Path(model)
        if not model.is_file():
            raise FileNotFoundError(f"Model file was not found: {model}")
        if self.settings.cli_path is None or not self.settings.cli_path.is_file():
            raise ValueError("Creality Print was not found. Set K2_CLI to its executable path.")
        if self.settings.profiles_path is None:
            raise ValueError("Profile root is not configured. Set K2_PROFILES.")

        catalog = ProfileCatalog(self.settings.profiles_path).list_for_nozzle(nozzle)
        machine_name, machine = _pick_machine(catalog["machine"], nozzle)
        process_name, process_path = _pick(catalog["process"], process, nozzle)
        filament_name, filament_path = _pick(catalog["filament"], material, nozzle)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        process_settings = _load_inheritance(process_path)
        applied, ignored = _apply_known_overrides(process_settings, overrides or {})
        process_settings["name"] = f"{process_name} (local MCP)"
        process_copy = output_dir / "process.json"
        process_copy.write_text(json.dumps(process_settings, ensure_ascii=False, indent=2), encoding="utf-8")

        command = [
            str(self.settings.cli_path),
            "--load-settings",
            f"{machine};{process_copy}",
            "--load-filaments",
            str(filament_path),
            "--slice",
            "0",
            "--outputdir",
            str(output_dir),
            str(model),
        ]
        return {
            "command": command,
            "machine": machine_name,
            "process": process_name,
            "filament": filament_name,
            "applied_overrides": applied,
            "ignored_overrides": ignored,
        }


def _pick(profiles: Mapping[str, Path], requested: str, nozzle: str) -> tuple[str, Path]:
    if not profiles:
        raise ValueError(f"No profiles were found for nozzle {nozzle}.")
    requested_lower = requested.lower()
    for name, path in profiles.items():
        if requested_lower in name.lower():
            return name, path
    raise ValueError(f"No profile matching '{requested}' was found for nozzle {nozzle}.")


def _pick_machine(profiles: Mapping[str, Path], nozzle: str) -> tuple[str, Path]:
    if not profiles:
        raise ValueError(f"No machine profile was found for nozzle {nozzle}.")
    name = sorted(profiles)[0]
    return name, profiles[name]


def _load_inheritance(path: Path) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    visited: set[Path] = set()
    current = Path(path)
    while current.is_file() and current not in visited:
        visited.add(current)
        payload = json.loads(current.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Profile is not a JSON object: {current.name}")
        merged = {**payload, **merged}
        parent = payload.get("inherits")
        current = current.parent / f"{parent}.json" if isinstance(parent, str) and parent else Path()
    return merged


def _apply_known_overrides(
    settings: dict[str, Any], overrides: Mapping[str, Any]
) -> tuple[dict[str, str | list[str]], list[str]]:
    applied: dict[str, str | list[str]] = {}
    ignored: list[str] = []
    for key, value in overrides.items():
        if key not in settings:
            ignored.append(key)
            continue
        normalized = [str(item) for item in value] if isinstance(value, list) else str(value)
        settings[key] = normalized
        applied[key] = normalized
    return applied, ignored
