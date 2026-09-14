"""Small Moonraker HTTP client used by the K2 adapter.

All requests ignore ambient proxy settings. A printer normally lives on the
same local network, where an inherited corporate or system proxy is incorrect.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import httpx


class MoonrakerClient:
    def __init__(self, base_url: str, *, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get_objects(self, object_names: Iterable[str]) -> dict[str, Any]:
        names = tuple(object_names)
        if not names:
            raise ValueError("At least one Moonraker object name is required.")

        query = "&".join(names)
        url = f"{self.base_url}/printer/objects/query?{query}"
        with httpx.Client(timeout=self.timeout_seconds, trust_env=False) as client:
            response = client.get(url)
            response.raise_for_status()

        payload = response.json()
        try:
            status = payload["result"]["status"]
        except (KeyError, TypeError) as exc:
            raise ValueError("Moonraker returned an unexpected status response.") from exc
        if not isinstance(status, dict):
            raise ValueError("Moonraker returned an invalid status object.")
        return status

    def get_path(self, path: str, **params: Any) -> dict[str, Any]:
        """Get a Moonraker endpoint and return its ``result`` object."""
        with httpx.Client(timeout=self.timeout_seconds, trust_env=False) as client:
            response = client.get(f"{self.base_url}{path}", params=params or None)
            response.raise_for_status()
        payload = response.json()
        result = payload.get("result") if isinstance(payload, dict) else None
        if not isinstance(result, dict):
            raise ValueError("Moonraker returned an unexpected endpoint response.")
        return result

    def post_path(self, path: str, **params: Any) -> dict[str, Any]:
        """Post to an explicitly selected Moonraker endpoint."""
        with httpx.Client(timeout=self.timeout_seconds, trust_env=False) as client:
            response = client.post(f"{self.base_url}{path}", params=params or None)
            response.raise_for_status()
        payload = response.json()
        result = payload.get("result") if isinstance(payload, dict) else None
        return result if isinstance(result, dict) else {}
