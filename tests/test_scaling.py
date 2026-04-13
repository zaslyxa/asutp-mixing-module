from mixing_module.material_db import init_material_db, list_components
from mixing_module.scaling import RecipeRow, scaling_engine


def test_material_db_seeds_components(tmp_path) -> None:
    db = tmp_path / "materials.db"
    init_material_db(db)
    items = list_components(db)
    assert len(items) >= 5


def test_scaling_engine_returns_model_parameters(tmp_path) -> None:
    db = tmp_path / "materials.db"
    init_material_db(db)
    items = list_components(db)
    rows = [RecipeRow(component=items[0], mass_kg=60), RecipeRow(component=items[1], mass_kg=40)]

    result = scaling_engine(rows, rotor_speed=1.2, q_l_target=0.3, cell_volume_m3=0.8)

    assert result["model"]["k"] > 0
    assert result["model"]["pe"] > 0
    assert result["model"]["ka"] > 0
    assert result["model"]["kh"] > 0
    assert result["model"]["b_q"] > 0
