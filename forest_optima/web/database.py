# -*- coding: utf-8 -*-
"""
Модуль персистентного хранения данных пользователей (Workspaces / Сценарии расчетов).
Реализует строгую изоляцию пользователей (User / Tenant Scoping) на базе SQLite (WAL).
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
    """Инициализация и автоматическая миграция схемы базы данных."""
    with _get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                uid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                data_json TEXT NOT NULL,
                owner_id TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # Миграция существующей схемы при отсутствии столбца owner_id
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(workspaces);")
        columns = [row["name"] for row in cursor.fetchall()]
        if "owner_id" not in columns:
            cursor.execute("ALTER TABLE workspaces ADD COLUMN owner_id TEXT NOT NULL DEFAULT '';")

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspaces_updated_at
            ON workspaces(updated_at DESC);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspaces_owner
            ON workspaces(owner_id, updated_at DESC);
        """)
        conn.commit()


def upsert_workspace(
    db_path: Path | str,
    uid: str,
    name: str,
    data: dict[str, Any],
    owner_id: str = "",
) -> dict[str, Any]:
    """
    Сохранение или обновление рабочего пространства.
    Связывает сценарий с владельцем (owner_id).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    data_json = json.dumps(data, ensure_ascii=False)

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT created_at, owner_id FROM workspaces WHERE uid = ?;", (uid,))
        row = cursor.fetchone()

        if row:
            created_at = row["created_at"]
            # Сохраняем исходного владельца, если передан пустой owner_id
            effective_owner = owner_id if owner_id else row["owner_id"]
            cursor.execute(
                """
                UPDATE workspaces
                SET name = ?, data_json = ?, owner_id = ?, updated_at = ?
                WHERE uid = ?;
                """,
                (name, data_json, effective_owner, now_iso, uid),
            )
        else:
            created_at = now_iso
            cursor.execute(
                """
                INSERT INTO workspaces (uid, name, data_json, owner_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (uid, name, data_json, owner_id, created_at, now_iso),
            )
        conn.commit()

    return {
        "uid": uid,
        "name": name,
        "data": data,
        "owner_id": owner_id,
        "created_at": created_at,
        "updated_at": now_iso,
    }


def get_workspace(db_path: Path | str, uid: str) -> dict[str, Any] | None:
    """Получение данных рабочего пространства по уникальному идентификатору."""
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT uid, name, data_json, owner_id, created_at, updated_at FROM workspaces WHERE uid = ?;",
            (uid,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "uid": row["uid"],
            "name": row["name"],
            "data": json.loads(row["data_json"]),
            "owner_id": row["owner_id"] if "owner_id" in row.keys() else "",
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def list_workspaces(
    db_path: Path | str,
    owner_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, str]]:
    """
    Список сохраненных рабочих пространств, принадлежащих конкретному пользователю.
    Защищает от утечки чужих данных: без owner_id возвращает пустой список.
    """
    if not owner_id or not owner_id.strip():
        return []

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT uid, name, created_at, updated_at
            FROM workspaces
            WHERE owner_id = ?
            ORDER BY updated_at DESC
            LIMIT ?;
            """,
            (owner_id.strip(), limit),
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


def delete_workspace(db_path: Path | str, uid: str, owner_id: str | None = None) -> bool:
    """Удаление рабочего пространства с проверкой владельца при наличии."""
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        if owner_id and owner_id.strip():
            cursor.execute(
                "DELETE FROM workspaces WHERE uid = ? AND (owner_id = ? OR owner_id = '');",
                (uid, owner_id.strip()),
            )
        else:
            cursor.execute("DELETE FROM workspaces WHERE uid = ?;", (uid,))
        conn.commit()
        return cursor.rowcount > 0
