"""Registry store — semver manifests and module pins."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$")


class RegistryStore:
    def __init__(self, db_path: Path | None = None) -> None:
        from raphael_contracts import db as rdb

        self._postgres = rdb.is_postgres()
        if self._postgres:
            rdb.ensure_migrations()
        else:
            self._db = db_path or Path(os.environ.get("RAPHAEL_REGISTRY_DB", "/tmp/raphael-registry.db"))
            self._db.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self._db, check_same_thread=False)
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS registry_entries (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    manifest TEXT NOT NULL DEFAULT '{}',
                    module_pins TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                )"""
            )
            self._conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _validate_version(version: str) -> None:
        if not _SEMVER.match(version):
            raise ValueError("invalid_semver")

    def list(self) -> list[dict[str, Any]]:
        if self._postgres:
            from raphael_contracts import db as rdb

            rows = rdb.pg_fetchall(
                "SELECT id, name, version, manifest, module_pins, created_at FROM registry_entries ORDER BY created_at DESC",
            )
        else:
            rows = self._conn.execute(
                "SELECT id, name, version, manifest, module_pins, created_at FROM registry_entries ORDER BY created_at DESC",
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get(self, entry_id: str) -> dict[str, Any] | None:
        if self._postgres:
            from raphael_contracts import db as rdb

            row = rdb.pg_fetchone(
                "SELECT id, name, version, manifest, module_pins, created_at FROM registry_entries WHERE id = %s",
                (entry_id,),
            )
        else:
            row = self._conn.execute(
                "SELECT id, name, version, manifest, module_pins, created_at FROM registry_entries WHERE id = ?",
                (entry_id,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def create(
        self,
        *,
        name: str,
        version: str,
        manifest: dict[str, Any] | None = None,
        module_pins: list[dict[str, str]] | None = None,
        entry_id: str | None = None,
    ) -> dict[str, Any]:
        self._validate_version(version)
        eid = entry_id or f"reg-{uuid.uuid4().hex[:10]}"
        now = self._now()
        manifest_json = json.dumps(manifest or {})
        pins_json = json.dumps(module_pins or [])
        if self._postgres:
            from raphael_contracts import db as rdb

            rdb.pg_execute(
                "INSERT INTO registry_entries (id, name, version, manifest, module_pins, created_at) "
                "VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s)",
                (eid, name, version, manifest_json, pins_json, now),
            )
        else:
            self._conn.execute(
                "INSERT INTO registry_entries (id, name, version, manifest, module_pins, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (eid, name, version, manifest_json, pins_json, now),
            )
            self._conn.commit()
        return self.get(eid) or {"id": eid, "name": name, "version": version, "created_at": now}

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        if isinstance(row, dict):
            manifest = row.get("manifest")
            pins = row.get("module_pins")
            if isinstance(manifest, str):
                manifest = json.loads(manifest)
            if isinstance(pins, str):
                pins = json.loads(pins)
            return {
                "id": row["id"],
                "name": row["name"],
                "version": row["version"],
                "manifest": manifest or {},
                "module_pins": pins or [],
                "created_at": str(row.get("created_at") or ""),
            }
        manifest = json.loads(row[3] or "{}")
        pins = json.loads(row[4] or "[]")
        return {
            "id": row[0],
            "name": row[1],
            "version": row[2],
            "manifest": manifest,
            "module_pins": pins,
            "created_at": row[5],
        }
