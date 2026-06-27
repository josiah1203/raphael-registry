"""API routes for raphael-registry — semver manifests and module pins."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from raphael_registry.store import RegistryStore

router = APIRouter(tags=["raphael-registry"])
_store = RegistryStore()


def _publish_event(event_type: str, data: dict[str, Any]) -> None:
    try:
        from raphael_contracts.kafka import publish_event

        publish_event(event_type, data, source="raphael-registry")
    except Exception:
        pass


@router.get("")
def list_entries() -> dict[str, Any]:
    return {"service": "raphael-registry", "items": _store.list()}


@router.post("")
def create_entry(body: dict[str, Any]) -> dict[str, Any]:
    name = body.get("name") or body.get("id", "entry")
    version = body.get("version", "0.1.0")
    try:
        entry = _store.create(
            name=name,
            version=version,
            manifest=body.get("manifest"),
            module_pins=body.get("module_pins"),
            entry_id=body.get("id"),
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    _publish_event(
        "raphael.registry.published",
        {
            "id": entry["id"],
            "name": entry["name"],
            "version": entry["version"],
            "module_pins": entry.get("module_pins", []),
            "created_at": entry.get("created_at"),
        },
    )
    return entry


@router.get("/{entry_id}")
def get_entry(entry_id: str) -> dict[str, Any]:
    row = _store.get(entry_id)
    if not row:
        raise HTTPException(404, detail="not_found")
    return row
