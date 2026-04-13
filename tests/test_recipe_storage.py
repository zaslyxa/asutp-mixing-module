from pathlib import Path

from mixing_module.recipe_storage import load_recipe, save_recipe


def test_json_recipe_roundtrip(tmp_path: Path) -> None:
    payload = {
        "model": "wet-cascade",
        "shared": {"cells": 3, "tau_s": 45.0},
        "wet": {"component_inlet": [1.0, 0.2], "reaction_enabled": True},
    }
    path = tmp_path / "recipe.json"
    save_recipe(path, payload)
    loaded = load_recipe(path)
    assert loaded == payload


def test_yaml_recipe_roundtrip(tmp_path: Path) -> None:
    payload = {
        "model": "dry-cascade",
        "shared": {"cells": 4, "tau_s": 60.0},
    }
    path = tmp_path / "recipe.yaml"
    save_recipe(path, payload)
    loaded = load_recipe(path)
    assert loaded == payload
