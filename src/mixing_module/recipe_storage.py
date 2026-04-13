from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _normalize(path: str | Path) -> Path:
    return Path(path).expanduser()


def load_recipe(path: str | Path) -> dict[str, Any]:
    file_path = _normalize(path)
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return json.loads(file_path.read_text(encoding="utf-8"))
    if suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError("PyYAML is required for YAML recipe loading") from exc
        return yaml.safe_load(file_path.read_text(encoding="utf-8"))
    raise ValueError("Unsupported recipe format. Use .json, .yaml, or .yml")


def save_recipe(path: str | Path, payload: dict[str, Any]) -> None:
    file_path = _normalize(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return
    if suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError("PyYAML is required for YAML recipe saving") from exc
        file_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return
    raise ValueError("Unsupported recipe format. Use .json, .yaml, or .yml")
