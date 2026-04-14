from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _slug(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_") or "recipe"


def _versions_dir(base_dir: str | Path = "config/recipe_versions") -> Path:
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(frozen=True)
class RecipeRevision:
    revision_id: str
    recipe_name: str
    created_at: str
    payload: dict[str, Any]
    note: str = ""


def save_recipe_revision(
    recipe_name: str,
    payload: dict[str, Any],
    *,
    note: str = "",
    base_dir: str | Path = "config/recipe_versions",
) -> Path:
    versions_dir = _versions_dir(base_dir)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    revision_id = f"{_slug(recipe_name)}-{stamp}"
    body = {
        "revision_id": revision_id,
        "recipe_name": recipe_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": note,
        "payload": payload,
    }
    path = versions_dir / f"{revision_id}.json"
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_recipe_revisions(
    *,
    recipe_name: str | None = None,
    base_dir: str | Path = "config/recipe_versions",
) -> list[RecipeRevision]:
    versions_dir = _versions_dir(base_dir)
    result: list[RecipeRevision] = []
    for path in sorted(versions_dir.glob("*.json"), reverse=True):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if recipe_name and raw.get("recipe_name") != recipe_name:
            continue
        result.append(
            RecipeRevision(
                revision_id=str(raw.get("revision_id", path.stem)),
                recipe_name=str(raw.get("recipe_name", "")),
                created_at=str(raw.get("created_at", "")),
                note=str(raw.get("note", "")),
                payload=dict(raw.get("payload", {})),
            )
        )
    return result


def load_recipe_revision(
    revision_id: str,
    *,
    base_dir: str | Path = "config/recipe_versions",
) -> RecipeRevision:
    path = _versions_dir(base_dir) / f"{revision_id}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return RecipeRevision(
        revision_id=str(raw.get("revision_id", revision_id)),
        recipe_name=str(raw.get("recipe_name", "")),
        created_at=str(raw.get("created_at", "")),
        note=str(raw.get("note", "")),
        payload=dict(raw.get("payload", {})),
    )


def diff_recipe_revisions(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    changed: dict[str, dict[str, Any]] = {}
    keys = set(left.keys()) | set(right.keys())
    for key in sorted(keys):
        l_val = left.get(key, "<missing>")
        r_val = right.get(key, "<missing>")
        if l_val != r_val:
            changed[key] = {"left": l_val, "right": r_val}
    return {"changed_count": len(changed), "changes": changed}
