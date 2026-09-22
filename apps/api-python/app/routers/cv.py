from __future__ import annotations
import io
import json
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.ids import new_id
from app.core.security import get_current_user, CurrentUser
from app.models.cv import CvFile

router = APIRouter(prefix="/cv", tags=["CV / Profile"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "cv")
os.makedirs(UPLOAD_DIR, exist_ok=True)

SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "react", "nextjs", "fastapi",
    "django", "postgresql", "mysql", "aws", "docker", "kubernetes",
    "seo", "google ads", "email marketing", "crm", "automation",
    "figma", "photoshop", "ui/ux", "branding", "copywriting",
]


@router.get("")
async def list_cv(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CvFile)
        .where(CvFile.workspace_id == current.workspace_id)
        .order_by(CvFile.uploaded_at.desc())
    )
    files = result.scalars().all()
    return [
        {
            "id": f.id, "filename": f.filename, "originalName": f.original_name,
            "mimeType": f.mime_type, "size": f.size,
            "extractedSkills": json.loads(f.extracted_skills or "[]"),
            "uploadedAt": f.uploaded_at.isoformat() if f.uploaded_at else None,
        }
        for f in files
    ]


@router.post("", status_code=201)
async def upload_cv(
    file: UploadFile = File(...),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    file_id = new_id()
    original_name = file.filename or "upload"
    ext = os.path.splitext(original_name)[1].lower()
    save_name = f"{file_id}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    with open(save_path, "wb") as f:
        f.write(content)

    extracted_text = ""
    mime = file.content_type or "application/octet-stream"

    if ext == ".pdf" or "pdf" in mime:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            pass
    elif ext in (".txt", ".md") or "text" in mime:
        extracted_text = content.decode("utf-8", errors="ignore")

    text_lower = extracted_text.lower()
    skills = [s for s in SKILL_KEYWORDS if s in text_lower]

    cv = CvFile(
        id=file_id,
        filename=save_name,
        original_name=original_name,
        mime_type=mime,
        size=len(content),
        extracted_text=extracted_text[:10000] if extracted_text else None,
        extracted_skills=json.dumps(skills),
        workspace_id=current.workspace_id,
    )
    db.add(cv)
    await db.commit()
    await db.refresh(cv)

    return {
        "id": cv.id, "filename": cv.filename, "originalName": cv.original_name,
        "mimeType": cv.mime_type, "size": cv.size,
        "extractedSkills": skills,
        "uploadedAt": cv.uploaded_at.isoformat() if cv.uploaded_at else None,
    }


@router.delete("/{cv_id}", status_code=204)
async def delete_cv(
    cv_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CvFile).where(CvFile.id == cv_id, CvFile.workspace_id == current.workspace_id)
    )
    cv = result.scalar_one_or_none()
    if not cv:
        raise HTTPException(404, "File not found")
    try:
        path = os.path.join(UPLOAD_DIR, cv.filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    await db.delete(cv)
    await db.commit()
