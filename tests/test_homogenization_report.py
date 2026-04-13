from mixing_module.homogenization_report import export_homogenization_report


def test_export_report_creates_file(tmp_path) -> None:
    out = tmp_path / "report.txt"
    path = export_homogenization_report(
        output_path=str(out),
        batch_id="B-001",
        rsd=3.1,
        lacey=0.95,
        h_rel=0.9,
        t_target_s=12.0,
        main_component="Component 1",
        top_contributor="Component 2",
    )
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "MIXING QUALITY REPORT" in text
