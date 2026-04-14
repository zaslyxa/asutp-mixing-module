from __future__ import annotations

from mixing_module.recipe_changelog import generate_recipe_changelog
from mixing_module.recipe_versioning import save_recipe_revision


def test_generate_recipe_changelog(tmp_path) -> None:
    base = tmp_path / "versions"
    save_recipe_revision("Dry mixing", {"model": "dry-cascade", "shared": {"tau_s": 40}}, base_dir=base)
    save_recipe_revision("Dry mixing", {"model": "dry-cascade", "shared": {"tau_s": 42}}, base_dir=base)
    out = generate_recipe_changelog(recipe_name="Dry mixing", base_dir=base, output_path=tmp_path / "changelog.md")
    text = out.read_text(encoding="utf-8")
    assert "Recipe Changelog: Dry mixing" in text
    assert "Changed keys:" in text
