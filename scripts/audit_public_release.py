"""Reject content that should never be part of a public source release."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys


PRIVATE_IP = re.compile(
    r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
)
USER_PATH = re.compile(
    r"(?i)(?:[A-Z]:\\" + "Users" + r"\\|/" + "Users" + r"/|/" + "home" + r"/)"
)
SUSPECT_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:[A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)[A-Z0-9_]*)\s*[=:]\s*['\"]?(?!YOUR_|REPLACE_|<)[^\s'\"]{8,}"
)
FORBIDDEN_SUFFIXES = {".gcode", ".3mf", ".stl", ".jpeg", ".jpg", ".png"}
TEXT_SUFFIXES = {"", ".md", ".py", ".toml", ".json", ".txt", ".yml", ".yaml", ".svg", ".ini"}
IGNORED_PARTS = {".git", "__pycache__", ".venv", "node_modules"}


@dataclass(frozen=True)
class AuditResult:
    errors: list[str]

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def audit(root: Path) -> AuditResult:
    root = Path(root).resolve()
    errors: list[str] = []
    for path in _files_to_scan(root):
        relative = path.relative_to(root)
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden artifact tracked: {relative}")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-text file requires manual review: {relative}")
            continue
        if PRIVATE_IP.search(content):
            errors.append(f"private network address found: {relative}")
        if USER_PATH.search(content):
            errors.append(f"personal user path found: {relative}")
        if SUSPECT_ASSIGNMENT.search(content):
            errors.append(f"possible secret assignment found: {relative}")
    return AuditResult(errors)


def _files_to_scan(root: Path) -> list[Path]:
    tracked = _git_tracked_files(root)
    if tracked is not None:
        return tracked
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.parts)
    ]


def _git_tracked_files(root: Path) -> list[Path] | None:
    if not (root / ".git").exists():
        return None
    process = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=False
    )
    if process.returncode != 0:
        return None
    return [root / entry for entry in process.stdout.decode("utf-8").split("\0") if entry]


def main() -> int:
    result = audit(Path.cwd())
    if not result.has_errors:
        print("Public-release audit passed.")
        return 0
    print("Public-release audit failed:")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
