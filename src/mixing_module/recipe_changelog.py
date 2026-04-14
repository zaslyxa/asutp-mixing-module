from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .recipe_versioning import diff_recipe_revisions, list_recipe_revisions


def generate_recipe_changelog(
    *,
    recipe_name: str,
    base_dir: str | Path = "config/recipe_versions",
    output_path: str | Path | None = None,
) -> Path:
    revisions = list_recipe_revisions(recipe_name=recipe_name, base_dir=base_dir)
    safe_name = "".join(ch.lower() if ch.isalnum() else "-" for ch in recipe_name).strip("-") or "recipe"
    if output_path is None:
        out = Path("reports") / f"recipe-changelog-{safe_name}.md"
    else:
        out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        f"# Recipe Changelog: {recipe_name}",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    if not revisions:
        lines.append("No revisions found.")
        out.write_text("\n".join(lines), encoding="utf-8")
        return out

    lines.append(f"Total revisions: {len(revisions)}")
    lines.append("")
    for idx, rev in enumerate(revisions):
        lines.append(f"## {rev.revision_id}")
        lines.append(f"- Created: {rev.created_at}")
        lines.append(f"- Note: {rev.note or '-'}")
        if idx < len(revisions) - 1:
            prev = revisions[idx + 1]
            diff = diff_recipe_revisions(prev.payload, rev.payload)
            lines.append(f"- Changed keys: {diff['changed_count']}")
            sample_keys = list(diff["changes"].keys())[:8]
            if sample_keys:
                lines.append(f"- Keys: {', '.join(sample_keys)}")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out
