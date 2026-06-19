"""API v1 router toplayıcı. Feature router'ları buraya mount edilir."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.imports import router as imports_router
from app.api.v1.records import router as records_router
from app.api.v1.sync import router as sync_router
from app.api.v1.validation import router as validation_router

api_router = APIRouter()


@api_router.get("/status", tags=["meta"])
def status() -> dict[str, str]:
    """v1 API sağlık/sürüm kontrolü — frontend bağlantı doğrulaması için."""
    return {"status": "ok", "api": "v1"}


api_router.include_router(imports_router, prefix="/imports", tags=["imports"])
api_router.include_router(records_router, prefix="/records", tags=["records"])
api_router.include_router(validation_router, prefix="/validation", tags=["validation"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(sync_router, prefix="/sync", tags=["sync"])
