from __future__ import annotations
import re
import time
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.ids import new_id
from app.core.validation import validate_password_strength
from app.core.security import hash_password, verify_password, create_access_token, get_current_user, CurrentUser
from app.models.user import User, Account
from app.models.workspace import Workspace, WorkspaceMember

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    workspace_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _make_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{slug}-{int(time.time() * 1000) % 100000}"


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = new_id()
    workspace_id = new_id()

    user = User(id=user_id, name=body.name, email=body.email)
    account = Account(
        id=new_id(), account_id=body.email, provider_id="credential",
        password=hash_password(body.password), user_id=user_id,
    )
    workspace = Workspace(
        id=workspace_id, name=body.workspace_name, slug=_make_slug(body.workspace_name),
    )
    member = WorkspaceMember(
        id=new_id(), role="owner", workspace_id=workspace_id, user_id=user_id,
    )

    db.add_all([user, account, workspace, member])
    await db.commit()

    token = create_access_token(user_id, workspace_id, body.email)
    return {
        "token": token,
        "user": {"id": user_id, "name": body.name, "email": body.email},
        "workspace": {"id": workspace_id, "name": body.workspace_name, "slug": workspace.slug},
    }


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    acc_result = await db.execute(
        select(Account).where(Account.user_id == user.id, Account.provider_id == "credential")
    )
    account = acc_result.scalar_one_or_none()
    if not account or not account.password or not verify_password(body.password, account.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    mem_result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.user_id == user.id).limit(1)
    )
    member = mem_result.scalar_one_or_none()
    workspace = None
    if member:
        ws_result = await db.execute(select(Workspace).where(Workspace.id == member.workspace_id))
        workspace = ws_result.scalar_one_or_none()

    workspace_id = workspace.id if workspace else "default"
    token = create_access_token(user.id, workspace_id, user.email)
    return {
        "token": token,
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "workspace": {"id": workspace.id, "name": workspace.name, "slug": workspace.slug} if workspace else None,
    }


@router.get("/me")
async def me(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    ws_result = await db.execute(select(Workspace).where(Workspace.id == current.workspace_id))
    workspace = ws_result.scalar_one_or_none()
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "workspace": {"id": workspace.id, "name": workspace.name, "slug": workspace.slug} if workspace else None,
    }

