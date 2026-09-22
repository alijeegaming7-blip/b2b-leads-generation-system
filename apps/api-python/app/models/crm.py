from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead
    from app.models.workspace import Workspace


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String, default="USD")
    stage: Mapped[str] = mapped_column(String, default="lead")
    probability: Mapped[int] = mapped_column(Integer, default=0)
    close_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    lost_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    won_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    lost_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    lead_id: Mapped[Optional[str]] = mapped_column(ForeignKey("leads.id"), nullable=True, unique=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))

    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="deal")
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="deals")
    meetings: Mapped[List["Meeting"]] = relationship("Meeting", back_populates="deal", cascade="all, delete-orphan")
    proposals: Mapped[List["Proposal"]] = relationship("Proposal", back_populates="deal", cascade="all, delete-orphan")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=30)
    meeting_type: Mapped[str] = mapped_column("type", String, default="call")
    status: Mapped[str] = mapped_column(String, default="scheduled")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    deal_id: Mapped[Optional[str]] = mapped_column(ForeignKey("deals.id"), nullable=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))

    deal: Mapped[Optional["Deal"]] = relationship("Deal", back_populates="meetings")
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="meetings")


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="USD")
    status: Mapped[str] = mapped_column(String, default="draft")
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    deal_id: Mapped[Optional[str]] = mapped_column(ForeignKey("deals.id"), nullable=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))

    deal: Mapped[Optional["Deal"]] = relationship("Deal", back_populates="proposals")
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="proposals")
