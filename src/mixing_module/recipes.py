from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecipePreset:
    name: str
    model: str
    note: str


RECIPE_PRESETS: tuple[RecipePreset, ...] = (
    RecipePreset(
        name="Dry powder blending",
        model="dry-cascade",
        note="No liquid binder injection; RTD dry cascade model.",
    ),
    RecipePreset(
        name="Wet granulation with binder",
        model="wet-cascade",
        note="Liquid injection and reduced PBM quality state are enabled.",
    ),
)


def recipe_names() -> list[str]:
    return [r.name for r in RECIPE_PRESETS]


def get_recipe(name: str) -> RecipePreset:
    for recipe in RECIPE_PRESETS:
        if recipe.name == name:
            return recipe
    raise ValueError(f"unknown recipe: {name}")
