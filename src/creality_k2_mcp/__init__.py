"""Local, safe-by-default MCP tools for verified Creality K2 printers."""

__version__ = "1.0.0"
"""Creality K2 MCP package."""

from .config import Settings
from .profiles import K2Profile

__all__ = ["K2Profile", "Settings"]
