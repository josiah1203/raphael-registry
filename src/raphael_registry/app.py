"""Raphael service: raphael-registry."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from raphael_contracts.errors import ErrorResponse
from raphael_registry.routes import router

app = FastAPI(
    title="raphael-registry",
    description="Open publish/install for adapters, workflows, agents, templates",
    version="0.1.0",
    openapi_url="/v1/registry/openapi.json" if "/v1/registry" else "/openapi.json",
)

app.include_router(router, prefix="/v1/registry" if "/v1/registry" else "")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "raphael-registry"}


@app.exception_handler(Exception)
async def unhandled(_request, exc: Exception) -> JSONResponse:
    err = ErrorResponse(code="internal_error", message=str(exc))
    return JSONResponse(status_code=500, content=err.model_dump())
