from __future__ import annotations

from mixing_module.recipe_versioning import (
    diff_recipe_revisions,
    list_recipe_revisions,
    load_recipe_revision,
    save_recipe_revision,
)


def test_recipe_revision_roundtrip(tmp_path) -> None:
    payload = {"model": "dry-cascade", "shared": {"tau_s": 40.0}}
    path = save_recipe_revision("Dry mixing", payload, note="test", base_dir=tmp_path)
    assert path.exists()
    revisions = list_recipe_revisions(base_dir=tmp_path)
    assert len(revisions) == 1
    loaded = load_recipe_revision(revisions[0].revision_id, base_dir=tmp_path)
    assert loaded.payload == payload


def test_recipe_revision_diff() -> None:
    left = {"model": "dry-cascade", "shared": {"tau_s": 40.0}}
    right = {"model": "wet-cascade", "shared": {"tau_s": 60.0}}
    diff = diff_recipe_revisions(left, right)
    assert diff["changed_count"] == 2
    assert "model" in diff["changes"]
