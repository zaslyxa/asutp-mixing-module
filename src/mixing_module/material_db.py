from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MaterialComponent:
    code: str
    name: str
    type: str
    d50: float
    span: float
    rho_bulk: float
    rho_true: float
    hausner_ratio: float
    w_initial: float
    w_crit: float
    cp: float
    angle_repose: float
    friction_steel: float
    segregation_idx: float
    w_equilibrium: float
    rsd0: float


DEFAULT_COMPONENTS: tuple[MaterialComponent, ...] = (
    MaterialComponent("CEM_I_425N", "Portland cement CEM I 42.5N", "binder", 30.0, 1.8, 1200, 3100, 1.22, 1.0, 12.0, 880, 35, 0.55, 0.35, 1.5, 100.0),
    MaterialComponent("SAND_063_125", "Quartz sand 0.63-1.25", "filler", 800.0, 2.2, 1600, 2650, 1.12, 0.2, 3.0, 830, 32, 0.45, 0.45, 0.2, 100.0),
    MaterialComponent("LIME_HYDR", "Hydrated lime", "additive", 10.0, 1.6, 500, 2200, 1.18, 1.0, 8.0, 900, 42, 0.60, 0.40, 2.0, 100.0),
    MaterialComponent("SP1_SUPER", "Superplasticizer SP-1", "additive", 50.0, 1.4, 600, 1400, 1.05, 0.3, 5.0, 1200, 30, 0.40, 0.20, 0.5, 100.0),
    MaterialComponent("SILOX_HYDRO", "Silox hydrophobizer", "additive", 80.0, 1.5, 550, 1300, 1.07, 0.2, 4.0, 1100, 32, 0.42, 0.18, 0.1, 100.0),
    MaterialComponent("CEM_M500", "Cement M500", "binder", 18.5, 1.8, 1450, 3100, 1.22, 0.8, 12.5, 880, 38, 0.55, 0.35, 0.6, 100.0),
    MaterialComponent("SAND_Q", "Quartz Sand 0.2-0.5", "filler", 320, 2.2, 1600, 2650, 1.12, 0.2, 5.0, 830, 33, 0.45, 0.45, 0.2, 100.0),
)


def _db_path(path: str | Path | None) -> Path:
    if path is None:
        return Path("config/materials.db")
    return Path(path)


def init_material_db(path: str | Path | None = None) -> Path:
    db_path = _db_path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS components (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                d50 REAL NOT NULL,
                span REAL NOT NULL,
                rho_bulk REAL NOT NULL,
                rho_true REAL NOT NULL DEFAULT 2500,
                hausner_ratio REAL NOT NULL,
                w_initial REAL NOT NULL,
                w_crit REAL NOT NULL,
                cp REAL NOT NULL,
                angle_repose REAL NOT NULL,
                friction_steel REAL NOT NULL DEFAULT 0.45,
                segregation_idx REAL NOT NULL DEFAULT 0.3,
                w_equilibrium REAL NOT NULL DEFAULT 0.0,
                rsd0 REAL NOT NULL DEFAULT 100.0
            )
            """
        )
        existing_columns = {
            row[1] for row in con.execute("PRAGMA table_info(components)").fetchall()
        }
        if "segregation_idx" not in existing_columns:
            con.execute("ALTER TABLE components ADD COLUMN segregation_idx REAL NOT NULL DEFAULT 0.3")
        if "w_equilibrium" not in existing_columns:
            con.execute("ALTER TABLE components ADD COLUMN w_equilibrium REAL NOT NULL DEFAULT 0.0")
        if "rho_true" not in existing_columns:
            con.execute("ALTER TABLE components ADD COLUMN rho_true REAL NOT NULL DEFAULT 2500")
        if "friction_steel" not in existing_columns:
            con.execute("ALTER TABLE components ADD COLUMN friction_steel REAL NOT NULL DEFAULT 0.45")
        if "rsd0" not in existing_columns:
            con.execute("ALTER TABLE components ADD COLUMN rsd0 REAL NOT NULL DEFAULT 100.0")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                payload TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for item in DEFAULT_COMPONENTS:
            con.execute(
                """
                INSERT OR IGNORE INTO components
                (code, name, type, d50, span, rho_bulk, rho_true, hausner_ratio, w_initial, w_crit, cp, angle_repose, friction_steel, segregation_idx, w_equilibrium, rsd0)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.code,
                    item.name,
                    item.type,
                    item.d50,
                    item.span,
                    item.rho_bulk,
                    item.rho_true,
                    item.hausner_ratio,
                    item.w_initial,
                    item.w_crit,
                    item.cp,
                    item.angle_repose,
                    item.friction_steel,
                    item.segregation_idx,
                    item.w_equilibrium,
                    item.rsd0,
                ),
            )
        con.commit()
    return db_path


def list_components(path: str | Path | None = None) -> list[MaterialComponent]:
    db_path = init_material_db(path)
    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            """
            SELECT code, name, type, d50, span, rho_bulk, rho_true, hausner_ratio, w_initial, w_crit, cp, angle_repose, friction_steel, segregation_idx, w_equilibrium, rsd0
            FROM components
            ORDER BY name
            """
        ).fetchall()
    return [MaterialComponent(*row) for row in rows]


def get_component_by_code(code: str, path: str | Path | None = None) -> MaterialComponent:
    db_path = init_material_db(path)
    with sqlite3.connect(db_path) as con:
        row = con.execute(
            """
            SELECT code, name, type, d50, span, rho_bulk, rho_true, hausner_ratio, w_initial, w_crit, cp, angle_repose, friction_steel, segregation_idx, w_equilibrium, rsd0
            FROM components
            WHERE code = ?
            """,
            (code,),
        ).fetchone()
    if row is None:
        raise ValueError(f"component not found: {code}")
    return MaterialComponent(*row)
