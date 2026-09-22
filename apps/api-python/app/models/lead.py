from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.campaign import Campaign
    from app.models.contact import Contact
    from app.models.email import EmailLog
    from app.models.outreach import OutreachApproval
    from app.models.crm import Deal


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rating: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, default="google_maps")
    reference_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    has_website: Mapped[bool] = mapped_column(Boolean, default=False)

    # Enhanced contact data — populated by connectors
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    social_media: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # JSON: {facebook, instagram, ...}
    additional_emails: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    score: Mapped[int] = mapped_column(Integer, default=0)
    icp_fit_score: Mapped[int] = mapped_column(Integer, default=0)
    intent_score: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[str] = mapped_column(String, default="LOW")
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    pipeline_stage: Mapped[str] = mapped_column(String, default="DISCOVER")

    sales_brief: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website_audit: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    opportunities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    matched_services: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    matched_case_study: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    researched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    marketing_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pitch_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    crm_status: Mapped[str] = mapped_column(String, default="new")
    crm_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    close_result: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    email_opened: Mapped[bool] = mapped_column(Boolean, default=False)
    email_replied: Mapped[bool] = mapped_column(Boolean, default=False)
    email_bounced: Mapped[bool] = mapped_column(Boolean, default=False)

    last_reply_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_reply_intent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_reply_sentiment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_reply_urgency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    conversation_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_reply_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    whatsapp_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    contact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("contacts.id"), nullable=True)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="leads")
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="leads")
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="leads")
    activities: Mapped[List["LeadActivity"]] = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
    follow_ups: Mapped[List["FollowUp"]] = relationship("FollowUp", back_populates="lead", cascade="all, delete-orphan")
    email_logs: Mapped[List["EmailLog"]] = relationship("EmailLog", back_populates="lead")
    outreach_queue: Mapped[List["OutreachApproval"]] = relationship("OutreachApproval", back_populates="lead")
    deal: Mapped[Optional["Deal"]] = relationship("Deal", back_populates="lead", uselist=False)


class LeadActivity(Base):
    __tablename__ = "lead_activities"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra: Mapped[Optional[str]] = mapped_column("metadata", Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"))
    lead: Mapped["Lead"] = relationship("Lead", back_populates="activities")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"))
    lead: Mapped["Lead"] = relationship("Lead", back_populates="follow_ups")
