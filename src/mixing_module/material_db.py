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
    hausner_ratio: float
    w_initial: float
    w_crit: float
    cp: float
    angle_repose: float
    segregation_idx: float
    w_equilibrium: float


DEFAULT_COMPONENTS: tuple[MaterialComponent, ...] = (
    MaterialComponent("CEM_M500", "Cement M500", "binder", 18.5, 1.8, 1450, 1.22, 0.8, 12.5, 880, 38, 0.35, 0.6),
    MaterialComponent("SAND_Q", "Quartz Sand 0.2-0.5", "filler", 320, 2.2, 1600, 1.12, 0.2, 5.0, 830, 33, 0.45, 0.2),
    MaterialComponent("SALT_TECH", "Technical Salt", "additive", 210, 1.6, 1180, 1.18, 0.1, 3.0, 860, 31, 0.25, 0.3),
    MaterialComponent("WATER", "Water", "binder", 1, 1.0, 1000, 1.0, 100.0, 100.0, 4180, 5, 0.0, 100.0),
    MaterialComponent("PVA_DISP", "PVA Dispersion", "binder", 20, 1.4, 1080, 1.05, 55.0, 65.0, 3000, 10, 0.15, 45.0),
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
                hausner_ratio REAL NOT NULL,
                w_initial REAL NOT NULL,
                w_crit REAL NOT NULL,
                cp REAL NOT NULL,
                angle_repose REAL NOT NULL,
                segregation_idx REAL NOT NULL DEFAULT 0.3,
                w_equilibrium REAL NOT NULL DEFAULT 0.0
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
                (code, name, type, d50, span, rho_bulk, hausner_ratio, w_initial, w_crit, cp, angle_repose, segregation_idx, w_equilibrium)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.code,
                    item.name,
                    item.type,
                    item.d50,
                    item.span,
                    item.rho_bulk,
                    item.hausner_ratio,
                    item.w_initial,
                    item.w_crit,
                    item.cp,
                    item.angle_repose,
                    item.segregation_idx,
                    item.w_equilibrium,
                ),
            )
        con.commit()
    return db_path


def list_components(path: str | Path | None = None) -> list[MaterialComponent]:
    db_path = init_material_db(path)
    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            """
            SELECT code, name, type, d50, span, rho_bulk, hausner_ratio, w_initial, w_crit, cp, angle_repose, segregation_idx, w_equilibrium
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
            SELECT code, name, type, d50, span, rho_bulk, hausner_ratio, w_initial, w_crit, cp, angle_repose, segregation_idx, w_equilibrium
            FROM components
            WHERE code = ?
            """,
            (code,),
        ).fetchone()
    if row is None:
        raise ValueError(f"component not found: {code}")
    return MaterialComponent(*row)
