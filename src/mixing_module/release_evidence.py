from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_release_evidence_zip(
    *,
    recipe_name: str,
    batch_id: str,
    mixer_id: str,
    opc_payload: dict[str, Any],
    thresholds: dict[str, Any],
    publish_bundle: dict[str, Any],
    h_curve_csv: str,
    changelog_markdown: str,
    output_path: str | Path | None = None,
) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    if output_path is None:
        out = Path("reports") / f"release-evidence-{batch_id}-{ts}.zip"
    else:
        out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "recipe_name": recipe_name,
        "batch_id": batch_id,
        "mixer_id": mixer_id,
        "schema_version": opc_payload.get("schema_version", "1.0.0"),
        "files": [
            "manifest.json",
            "opc_payload.json",
            "publish_bundle.json",
            "threshold_profile.json",
            "h_curve.csv",
            "recipe_changelog.md",
        ],
    }

    with zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        zf.writestr("opc_payload.json", json.dumps(opc_payload, indent=2, ensure_ascii=False))
        zf.writestr("publish_bundle.json", json.dumps(publish_bundle, indent=2, ensure_ascii=False))
        zf.writestr("threshold_profile.json", json.dumps(thresholds, indent=2, ensure_ascii=False))
        zf.writestr("h_curve.csv", h_curve_csv)
        zf.writestr("recipe_changelog.md", changelog_markdown)

    return out
