from __future__ import annotations

import sqlite3
from pathlib import Path

from .h_kinetics import HMixSample


def init_historian_db(path: str | Path = "config/historian.db") -> Path:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS h_curve (
                batch_id TEXT NOT NULL,
                ts REAL NOT NULL,
                h REAL NOT NULL,
                k_mix REAL NOT NULL,
                n REAL NOT NULL,
                d REAL NOT NULL,
                w REAL NOT NULL,
                q_s REAL NOT NULL,
                p REAL NOT NULL,
                ready INTEGER NOT NULL
            )
            """
        )
        con.commit()
    return db_path


def append_h_sample(batch_id: str, sample: HMixSample, path: str | Path = "config/historian.db") -> None:
    db_path = init_historian_db(path)
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            INSERT INTO h_curve (batch_id, ts, h, k_mix, n, d, w, q_s, p, ready)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                sample.t_s,
                sample.h,
                sample.k_mix,
                sample.n,
                sample.d,
                sample.w,
                sample.q_s,
                sample.p,
                int(sample.ready),
            ),
        )
        con.commit()


def list_batches(path: str | Path = "config/historian.db") -> list[str]:
    db_path = init_historian_db(path)
    with sqlite3.connect(db_path) as con:
        rows = con.execute("SELECT DISTINCT batch_id FROM h_curve ORDER BY batch_id DESC").fetchall()
    return [r[0] for r in rows]


def load_batch_curve(batch_id: str, path: str | Path = "config/historian.db") -> list[dict]:
    db_path = init_historian_db(path)
    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            """
            SELECT ts, h, k_mix, n, d, w, q_s, p, ready
            FROM h_curve
            WHERE batch_id = ?
            ORDER BY ts
            """,
            (batch_id,),
        ).fetchall()
    return [
        {
            "t_s": r[0],
            "h": r[1],
            "k_mix": r[2],
            "n": r[3],
            "d": r[4],
            "w": r[5],
            "q_s": r[6],
            "p": r[7],
            "ready": bool(r[8]),
        }
        for r in rows
    ]
