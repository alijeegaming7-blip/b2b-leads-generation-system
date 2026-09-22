from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.lead import Lead


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    search_queries: Mapped[str] = mapped_column(Text, default="[]")
    max_results: Mapped[int] = mapped_column(Integer, default=20)
    your_service: Mapped[str] = mapped_column(String, nullable=False)
    content_style: Mapped[str] = mapped_column(String, default="balanced")
    language: Mapped[str] = mapped_column(String, default="english")
    sources: Mapped[str] = mapped_column(String, default='["google_maps"]')
    status: Mapped[str] = mapped_column(String, default="draft")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    total_leads: Mapped[int] = mapped_column(Integer, default=0)
    priority_leads: Mapped[int] = mapped_column(Integer, default=0)
    high_quality_leads: Mapped[int] = mapped_column(Integer, default=0)
    average_score: Mapped[float] = mapped_column(Float, default=0.0)

    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="campaigns")
    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="campaign", cascade="all, delete-orphan")
