from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.campaign import Campaign
    from app.models.lead import Lead
    from app.models.contact import Contact
    from app.models.integration import Integration, ApiKey
    from app.models.email import EmailCampaign
    from app.models.cv import CvFile
    from app.models.knowledge import KnowledgeBaseItem, CaseStudy
    from app.models.crm import Deal, Meeting, Proposal
    from app.models.outreach import OutreachApproval


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    logo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    plan: Mapped[str] = mapped_column(String, default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    members: Mapped[List["WorkspaceMember"]] = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    campaigns: Mapped[List["Campaign"]] = relationship("Campaign", back_populates="workspace", cascade="all, delete-orphan")
    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="workspace", cascade="all, delete-orphan")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="workspace", cascade="all, delete-orphan")
    integrations: Mapped[List["Integration"]] = relationship("Integration", back_populates="workspace", cascade="all, delete-orphan")
    api_keys: Mapped[List["ApiKey"]] = relationship("ApiKey", back_populates="workspace", cascade="all, delete-orphan")
    email_campaigns: Mapped[List["EmailCampaign"]] = relationship("EmailCampaign", back_populates="workspace", cascade="all, delete-orphan")
    cv_files: Mapped[List["CvFile"]] = relationship("CvFile", back_populates="workspace", cascade="all, delete-orphan")
    knowledge_base: Mapped[List["KnowledgeBaseItem"]] = relationship("KnowledgeBaseItem", back_populates="workspace", cascade="all, delete-orphan")
    case_studies: Mapped[List["CaseStudy"]] = relationship("CaseStudy", back_populates="workspace", cascade="all, delete-orphan")
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="workspace", cascade="all, delete-orphan")
    meetings: Mapped[List["Meeting"]] = relationship("Meeting", back_populates="workspace", cascade="all, delete-orphan")
    proposals: Mapped[List["Proposal"]] = relationship("Proposal", back_populates="workspace", cascade="all, delete-orphan")
    outreach_queue: Mapped[List["OutreachApproval"]] = relationship("OutreachApproval", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    role: Mapped[str] = mapped_column(String, default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="memberships")
