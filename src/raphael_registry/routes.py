"""API routes for raphael-registry."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["raphael-registry"])


@router.get("")
def list_root() -> dict[str, str]:
  return {"service": "raphael-registry", "status": "stub"}
