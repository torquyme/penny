"""Discover and validate local module manifests without executing their code."""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from toolkit.sdk import API_VERSION


@dataclass(frozen=True)
class Module:
    id: str
    name: str
    version: str
    description: str
    category: str
    directory: Path
    entrypoint: Path
    inputs: list[dict[str, Any]]
    timeout: int


def read_module(directory: Path) -> Module:
    directory = directory.resolve()
    raw = json.loads((directory / "module.json").read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("manifest must be an object")
    if type(raw.get("api_version")) is not int or raw["api_version"] != API_VERSION:
        raise ValueError(f"api_version must be {API_VERSION}")
    for key in ("id", "name", "version", "description", "category", "entrypoint"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", raw["id"]):
        raise ValueError("id must use lowercase letters, numbers, underscores or hyphens")
    entry = (directory / raw["entrypoint"]).resolve()
    if not entry.is_relative_to(directory) or entry.suffix != ".py" or not entry.is_file():
        raise ValueError("entrypoint must be a Python file inside the module directory")
    fields = raw.get("inputs", [])
    if not isinstance(fields, list):
        raise ValueError("inputs must be a list")
    names = set()
    for item in fields:
        if not isinstance(item, dict):
            raise ValueError("each input must be an object")
        key = item.get("key", "")
        if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", key) or key in names:
            raise ValueError("input keys must be unique lowercase identifiers")
        names.add(key)
        if item.get("type") not in {"string", "integer", "boolean"}:
            raise ValueError(f"Unsupported input type: {key}")
        if not isinstance(item.get("label"), str) or not item["label"].strip():
            raise ValueError(f"input label is required: {key}")
        if "required" in item and type(item["required"]) is not bool:
            raise ValueError(f"required must be boolean: {key}")
    timeout = raw.get("timeout_seconds", 30)
    if type(timeout) is not int or not 1 <= timeout <= 300:
        raise ValueError("timeout_seconds must be between 1 and 300")
    module = Module(raw["id"], raw["name"], raw["version"], raw["description"],
                    raw["category"], directory, entry, fields, timeout)
    validate_inputs(module, {f["key"]: f["default"] for f in fields if "default" in f}, defaults_only=True)
    return module


def discover(root: Path) -> tuple[list[Module], list[str]]:
    modules, errors, seen = [], [], set()
    if not root.exists():
        return modules, [f"Module directory missing: {root}"]
    for manifest in sorted(root.glob("*/module.json")):
        try:
            module = read_module(manifest.parent)
            if module.id in seen:
                raise ValueError(f"Duplicate module id: {module.id}")
            seen.add(module.id)
            modules.append(module)
        except (ValueError, TypeError, OSError) as exc:
            errors.append(f"{manifest.parent.name}: {exc}")
    return modules, errors


def validate_inputs(module: Module, values: dict, defaults_only: bool = False) -> dict:
    known = {f["key"] for f in module.inputs}
    if set(values) - known:
        raise ValueError("Unknown input fields")
    validated = {}
    for spec in module.inputs:
        key = spec["key"]
        value = values.get(key, spec.get("default"))
        if value is None or (isinstance(value, str) and not value.strip()):
            if spec.get("required", False) and not defaults_only:
                raise ValueError(f"{spec['label']} is required")
            continue
        expected = {"string": str, "integer": int, "boolean": bool}[spec["type"]]
        if type(value) is not expected:
            raise ValueError(f"{spec['label']} must be {spec['type']}")
        validated[key] = value
    return validated
