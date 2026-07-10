"""Persisted database models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from blackjack.db.database import Base


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    kind: Mapped[str] = mapped_column(index=True)  # "basic" | "counting"
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    statistics: Mapped[dict[str, Any]] = mapped_column(JSON)
    rounds_played: Mapped[int]
    ruined: Mapped[bool]
