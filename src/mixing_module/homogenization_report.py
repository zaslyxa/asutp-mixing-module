from __future__ import annotations

from pathlib import Path


def export_homogenization_report(
    *,
    output_path: str,
    batch_id: str,
    rsd: float,
    lacey: float,
    h_rel: float,
    t_target_s: float,
    main_component: str,
    top_contributor: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "MIXING QUALITY REPORT",
            f"Batch: {batch_id}",
            "",
            f"RSD: {rsd:.3f}%",
            f"Lacey Index: {lacey:.3f}",
            f"H_rel: {h_rel:.3f}",
            f"Predicted t_target: {t_target_s:.1f} s",
            f"Main component: {main_component}",
            f"Top heterogeneity contributor: {top_contributor}",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return path
