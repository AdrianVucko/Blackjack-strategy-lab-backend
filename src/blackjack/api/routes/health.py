"""Health and metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from blackjack import __version__
from blackjack.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__, "environment": settings.environment}
