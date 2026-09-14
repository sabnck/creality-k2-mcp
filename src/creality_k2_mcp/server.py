"""MCP presentation layer for safe Creality K2 access."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
from mcp.server.mcpserver import Image, MCPServer

from .analysis import analyze_3mf, analyze_gcode
from .config import Settings
from .moonraker import MoonrakerClient
from .profiles import K2Profile
from .setup_prompt import SETUP_PROMPT
from .slicer import ProfileCatalog, SlicePlanner
from .status import duration_hms, remaining_seconds


class PrinterService:
    """Testable service layer. Named controls are the only write operations."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: MoonrakerClient | Any | None = None,
        snapshot_fetcher: Callable[[], bytes | None] | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or MoonrakerClient(settings.base_url)
        self.profile = K2Profile()
        self._snapshot_fetcher = snapshot_fetcher or self._fetch_snapshot
        self._write_verified = False

    def printer_status(self) -> dict[str, Any]:
        status = self.profile.normalize_status(self.client.get_objects(self.profile.object_names))
        progress = status.get("progress_percent")
        progress_fraction = progress / 100 if isinstance(progress, (int, float)) else None
        status["elapsed"] = duration_hms(status.get("elapsed_seconds"))
        status["remaining"] = duration_hms(
            remaining_seconds(status.get("elapsed_seconds"), progress_fraction)
        )
        return status

    def snapshot(self) -> Image | str:
        image_bytes = self._snapshot_fetcher()
        if image_bytes and image_bytes[:2] == b"\xff\xd8":
            return Image(data=image_bytes, format="jpeg")
        return "Camera snapshot is unavailable. Check K2_CAM_PORT and camera access."

    def job_history(self, limit: int = 10) -> list[dict[str, Any]]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100.")
        result = self.client.get_path("/server/history/list", limit=limit, order="desc")
        jobs = result.get("jobs", [])
        if not isinstance(jobs, list):
            return []
        return [
            {
                "file": job.get("filename"),
                "status": job.get("status"),
                "duration": duration_hms(job.get("total_duration")),
                "filament_m": round(float(job.get("filament_used", 0)) / 1000, 2),
            }
            for job in jobs
            if isinstance(job, dict)
        ]

    def recent_logs(self, count: int = 40) -> list[dict[str, str | None]]:
        if not 1 <= count <= 500:
            raise ValueError("count must be between 1 and 500.")
        result = self.client.get_path("/server/gcode_store", count=count)
        messages = result.get("gcode_store", [])
        return [
            {"type": entry.get("type"), "message": entry.get("message")}
            for entry in messages
            if isinstance(entry, dict)
        ]

    def catalog(self, nozzle: str) -> dict[str, list[str]]:
        if self.settings.profiles_path is None:
            raise ValueError("Profile root is not configured. Set K2_PROFILES.")
        catalog = ProfileCatalog(self.settings.profiles_path).list_for_nozzle(nozzle)
        return {kind: sorted(entries) for kind, entries in catalog.items()}

    def model_info(self, path: str) -> dict[str, Any]:
        return analyze_3mf(Path(path))

    def gcode_info(self, path: str) -> dict[str, Any]:
        return analyze_gcode(Path(path))

    def search_settings(self, path: str, query: str) -> dict[str, Any]:
        query = query.strip().lower()
        if not query:
            raise ValueError("query must not be empty.")
        settings = analyze_3mf(Path(path))["settings"]
        return {key: value for key, value in settings.items() if query in key.lower()}

    def slice_plan(
        self,
        model: str,
        nozzle: str,
        material: str,
        process: str,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a local, reviewable Creality Print command without running it."""
        return SlicePlanner(self.settings).prepare(
            model=Path(model),
            nozzle=nozzle,
            material=material,
            process=process,
            overrides=overrides,
            output_dir=self.settings.work_dir / "slice-plans",
        )

    def pause_print(self) -> str:
        return self._write("/printer/print/pause", "Print paused.")

    def resume_print(self) -> str:
        return self._write("/printer/print/resume", "Print resumed.")

    def cancel_print(self, confirm: str = "") -> str:
        if confirm.strip().upper() != "CONFIRM":
            return "Print was not cancelled. Repeat with confirm='CONFIRM'."
        return self._write("/printer/print/cancel", "Print cancelled.")

    def set_temperature(self, heater: str, celsius: float) -> str:
        if heater == "nozzle":
            maximum, command = self.settings.max_nozzle_c, f"M104 S{celsius:.0f}"
        elif heater == "bed":
            maximum, command = self.settings.max_bed_c, f"M140 S{celsius:.0f}"
        else:
            return "heater must be 'nozzle' or 'bed'."
        if not 0 <= celsius <= maximum:
            return f"Refused: {heater} temperature must be between 0 and {maximum:g} C."
        return self._write("/printer/gcode/script", f"{heater} target set to {celsius:.0f} C.", script=command)

    def set_speed_factor(self, percent: int) -> str:
        if not 30 <= percent <= 150:
            return "Refused: speed must be between 30 and 150 percent."
        return self._write("/printer/gcode/script", f"Speed set to {percent} percent.", script=f"M220 S{percent}")

    def set_fan(self, percent: int) -> str:
        if not 0 <= percent <= 100:
            return "Refused: fan must be between 0 and 100 percent."
        return self._write("/printer/gcode/script", f"Model fan set to {percent} percent.", script=f"M106 S{round(percent * 2.55)}")

    def _write(self, path: str, message: str, **params: Any) -> str:
        if not self.settings.allow_write:
            return "Printer control is disabled. Set K2_ALLOW_WRITE=1 only after you choose to allow it."
        if not self._write_verified:
            try:
                objects = self.client.get_objects(self.profile.object_names)
            except Exception:
                return "Printer control is refused until K2 capabilities can be verified by a read-only check."
            required = {"virtual_sdcard", "output_pin fan0", "output_pin fan2"}
            if not required.issubset(objects):
                return "Printer control is refused because K2 capabilities were not verified by the read-only check."
            self._write_verified = True
        self.client.post_path(path, **params)
        return message

    def _fetch_snapshot(self) -> bytes | None:
        urls = (
            f"http://{self.settings.host}:{self.settings.camera_port}/?action=snapshot",
            f"http://{self.settings.host}/webcam/?action=snapshot",
            f"http://{self.settings.host}:8000/?action=snapshot",
        )
        for url in urls:
            try:
                with httpx.Client(timeout=8, trust_env=False) as client:
                    response = client.get(url)
                if response.status_code == 200 and response.content[:2] == b"\xff\xd8":
                    return response.content
            except httpx.HTTPError:
                continue
        return None


def create_server(settings: Settings | None = None) -> MCPServer:
    settings = settings or Settings.from_env()
    service = PrinterService(settings)
    server = MCPServer(
        name="creality-k2-mcp",
        title="Creality K2 MCP",
        description="Local, K2-verified printer context for MCP clients.",
        instructions=SETUP_PROMPT,
        version="1.0.0",
    )

    server.tool()(service.printer_status)
    server.tool()(service.snapshot)
    server.tool()(service.job_history)
    server.tool()(service.recent_logs)
    server.tool()(service.catalog)
    server.tool(name="model_info")(service.model_info)
    server.tool(name="gcode_info")(service.gcode_info)
    server.tool()(service.search_settings)
    server.tool()(service.slice_plan)
    server.tool()(service.pause_print)
    server.tool()(service.resume_print)
    server.tool()(service.cancel_print)
    server.tool()(service.set_temperature)
    server.tool()(service.set_speed_factor)
    server.tool()(service.set_fan)
    return server


def main() -> None:
    create_server().run(transport="stdio")
