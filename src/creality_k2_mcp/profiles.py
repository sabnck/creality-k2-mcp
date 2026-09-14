"""Printer-specific translation from Moonraker objects to stable MCP data."""

from __future__ import annotations

from typing import Any


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _number(value: Any) -> float | int | None:
    return value if isinstance(value, (float, int)) and not isinstance(value, bool) else None


class K2Profile:
    """Normalization rules verified against a Creality K2 Moonraker response."""

    object_names = (
        "extruder",
        "heater_bed",
        "print_stats",
        "virtual_sdcard",
        "gcode_move",
        "toolhead",
        "output_pin fan0",
        "output_pin fan2",
    )

    def normalize_status(self, raw_status: dict[str, Any]) -> dict[str, Any]:
        print_stats = _mapping(raw_status.get("print_stats"))
        virtual_sdcard = _mapping(raw_status.get("virtual_sdcard"))
        fan0 = _mapping(raw_status.get("output_pin fan0"))
        fan2 = _mapping(raw_status.get("output_pin fan2"))
        extruder = _mapping(raw_status.get("extruder"))
        heater_bed = _mapping(raw_status.get("heater_bed"))

        progress = _number(virtual_sdcard.get("progress"))
        return {
            "state": print_stats.get("state"),
            "file": print_stats.get("filename"),
            "elapsed_seconds": _number(print_stats.get("print_duration")),
            "progress_percent": round(progress * 100, 1) if progress is not None else None,
            "layer": {
                "current": _number(virtual_sdcard.get("layer")),
                "total": _number(virtual_sdcard.get("layer_count")),
            },
            "fans": {
                "model_percent": self._fan_percent(fan0),
                "side_percent": self._fan_percent(fan2),
            },
            "temperatures_c": {
                "nozzle": _number(extruder.get("temperature")),
                "nozzle_target": _number(extruder.get("target")),
                "bed": _number(heater_bed.get("temperature")),
                "bed_target": _number(heater_bed.get("target")),
            },
        }

    @staticmethod
    def _fan_percent(fan: dict[str, Any]) -> int | None:
        value = _number(fan.get("value"))
        return round(value * 100) if value is not None else None
