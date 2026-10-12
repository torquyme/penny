"""Stable, dependency-free API for toolkit modules (API version 1)."""
from dataclasses import dataclass, field
from typing import Any

API_VERSION = 1


@dataclass
class ModuleContext:
    """Per-run context. Return JSON-compatible data from run()."""

    run_id: str
    logs: list[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        self.logs.append(str(message))


def finding(title: str, description: str, severity: str = "info") -> dict[str, Any]:
    if severity not in {"info", "low", "medium", "high", "critical"}:
        raise ValueError("Unsupported severity")
    return {"title": title, "description": description, "severity": severity}
