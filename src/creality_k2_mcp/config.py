"""Configuration loaded from environment variables.

The package deliberately keeps local machine details outside version control.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from collections.abc import Mapping
import ipaddress


K2_HARD_MAX_NOZZLE_C = 280.0
K2_HARD_MAX_BED_C = 110.0


def _optional_path(name: str, values: Mapping[str, str]) -> Path | None:
    value = values.get(name, "").strip()
    return Path(value) if value else None


@dataclass(frozen=True)
class Settings:
    """Runtime settings for a local Moonraker-compatible printer."""

    host: str
    port: int = 7125
    allow_write: bool = False
    camera_port: int = 8080
    max_nozzle_c: float = 280.0
    max_bed_c: float = 110.0
    cli_path: Path | None = None
    profiles_path: Path | None = None
    work_dir: Path = Path("runtime")

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("K2_HOST is required. Set it to your printer's local address.")
        if not 1 <= self.port <= 65535:
            raise ValueError("K2_PORT must be between 1 and 65535.")
        if not 1 <= self.camera_port <= 65535:
            raise ValueError("K2_CAM_PORT must be between 1 and 65535.")
        if not 0 < self.max_nozzle_c <= K2_HARD_MAX_NOZZLE_C:
            raise ValueError(f"K2 nozzle maximum must be between 0 and {K2_HARD_MAX_NOZZLE_C:g} C.")
        if not 0 < self.max_bed_c <= K2_HARD_MAX_BED_C:
            raise ValueError(f"K2 bed maximum must be between 0 and {K2_HARD_MAX_BED_C:g} C.")

    @property
    def base_url(self) -> str:
        host = self.host.strip().strip("[]")
        try:
            is_ipv6 = ipaddress.ip_address(host).version == 6
        except ValueError:
            is_ipv6 = False
        return f"http://{'[' + host + ']' if is_ipv6 else host}:{self.port}"

    @classmethod
    def from_env(cls, values: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if values is None else values
        host = values.get("K2_HOST", "").strip()
        if not host:
            raise ValueError("K2_HOST is required. Set it to your printer's local address.")

        raw_port = values.get("K2_PORT", "7125").strip()
        try:
            port = int(raw_port)
        except ValueError as exc:
            raise ValueError("K2_PORT must be a valid TCP port.") from exc
        if not 1 <= port <= 65535:
            raise ValueError("K2_PORT must be between 1 and 65535.")

        return cls(
            host=host,
            port=port,
            allow_write=values.get("K2_ALLOW_WRITE", "0").strip() == "1",
            camera_port=_bounded_int(values.get("K2_CAM_PORT", "8080"), "K2_CAM_PORT"),
            max_nozzle_c=_positive_float(values.get("K2_MAX_NOZZLE", "280"), "K2_MAX_NOZZLE"),
            max_bed_c=_positive_float(values.get("K2_MAX_BED", "110"), "K2_MAX_BED"),
            cli_path=_optional_path("K2_CLI", values),
            profiles_path=_optional_path("K2_PROFILES", values),
            work_dir=_optional_path("K2_WORK", values) or Path("runtime"),
        )


def _bounded_int(value: str, name: str) -> int:
    try:
        parsed = int(value.strip())
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid TCP port.") from exc
    if not 1 <= parsed <= 65535:
        raise ValueError(f"{name} must be between 1 and 65535.")
    return parsed


def _positive_float(value: str, name: str) -> float:
    try:
        parsed = float(value.strip())
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return parsed
