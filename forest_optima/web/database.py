# -*- coding: utf-8 -*-
"""
Модуль персистентного хранения данных пользователей (Workspaces / Сценарии расчетов).
Реализован на базе легковесной встраиваемой СУБД SQLite с режимом WAL и потокобезопасностью.
"""

from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _get_connection(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db(db_path: Path | str) -> None:
    """Инициализация схемы базы данных."""
    with _get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                uid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspaces_updated_at
            ON workspaces(updated_at DESC);
        """)
        conn.commit()


def upsert_workspace(
    db_path: Path | str,
    uid: str,
    name: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Сохранение или обновление рабочего пространства пользователя."""
    now_iso = datetime.now(timezone.utc).isoformat()
    data_json = json.dumps(data, ensure_ascii=False)

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM workspaces WHERE uid = ?;", (uid,))
        row = cursor.fetchone()

        if row:
            created_at = row["created_at"]
            cursor.execute(
                """
                UPDATE workspaces
                SET name = ?, data_json = ?, updated_at = ?
                WHERE uid = ?;
                """,
                (name, data_json, now_iso, uid),
            )
        else:
            created_at = now_iso
            cursor.execute(
                """
                INSERT INTO workspaces (uid, name, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (uid, name, data_json, created_at, now_iso),
            )
        conn.commit()

    return {
        "uid": uid,
        "name": name,
        "data": data,
        "created_at": created_at,
        "updated_at": now_iso,
    }


def get_workspace(db_path: Path | str, uid: str) -> dict[str, Any] | None:
    """Получение данных рабочего пространства по уникальному идентификатору."""
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT uid, name, data_json, created_at, updated_at FROM workspaces WHERE uid = ?;",
            (uid,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "uid": row["uid"],
            "name": row["name"],
            "data": json.loads(row["data_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def list_workspaces(db_path: Path | str, limit: int = 50) -> list[dict[str, str]]:
    """Список последних сохраненных рабочих пространств."""
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT uid, name, created_at, updated_at
            FROM workspaces
            ORDER BY updated_at DESC
            LIMIT ?;
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            {
                "uid": r["uid"],
                "name": r["name"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]


def delete_workspace(db_path: Path | str, uid: str) -> bool:
    """Удаление рабочего пространства."""
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM workspaces WHERE uid = ?;", (uid,))
        conn.commit()
        return cursor.rowcount > 0
