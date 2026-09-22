"""Marketing AI — evidence-based, personalised pitch generation."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.ai.sales_research import SalesBrief
    from app.services.ai.service_recommendation import CaseStudyMatch, ServiceMatch

logger = logging.getLogger(__name__)


@dataclass
class MarketingContent:
    email_subject: str
    email_body: str
    whatsapp: str
    instagram: str
    linkedin_note: str
    cold_call_opening: str
    pitch_angle: str
    proof_point: Optional[str]


async def generate(
    business_name: str,
    industry: str,
    address: Optional[str] = None,
    rating: Optional[str] = None,
    has_website: bool = False,
    your_service: str = "digital services",
    content_style: str = "balanced",
    language: str = "english",
    score: int = 0,
    sales_brief: "Optional[SalesBrief]" = None,
    case_study: "Optional[CaseStudyMatch]" = None,
    top_service: "Optional[ServiceMatch]" = None,
) -> MarketingContent:
    try:
        from app.services.ai.provider import AI_AVAILABLE
        if AI_AVAILABLE:
            return await _ai_generate(
                business_name, industry, address, rating, has_website,
                your_service, content_style, language, score,
                sales_brief, case_study, top_service,
            )
    except Exception as exc:
        logger.error(f"AI pitch generation failed: {exc}")

    return _fallback(business_name, industry, rating, your_service, language, sales_brief, case_study, top_service)


async def _ai_generate(
    name: str, industry: str, address: Optional[str], rating: Optional[str],
    has_website: bool, your_service: str, content_style: str, language: str,
    score: int, brief: "Optional[SalesBrief]",
    case_study: "Optional[CaseStudyMatch]", top_service: "Optional[ServiceMatch]",
) -> MarketingContent:
    from app.services.ai.provider import complete_json

    styles = {
        "professional": "formal, professional, direct",
        "friendly":     "warm, friendly, approachable",
        "casual":       "casual, relaxed, conversational",
        "balanced":     "balanced, friendly yet professional",
    }
    style = styles.get(content_style, "balanced")
    is_id = language == "indonesian"
    top_pain = brief.pain_points[0] if brief and brief.pain_points else None
    talk_track = brief.talk_track_opener if brief else ""
    proof_line = f'Proof: "{case_study.title}" — {case_study.outcome}' if case_study else ""
    service_line = f"Primary offer: {top_service.service_name} — {top_service.description}" if top_service else f"Service: {your_service}"
    pain_line = f"Key pain: {top_pain.title} ({top_pain.evidence})" if top_pain else ""

    prompt = (
        f"Generate personalised B2B outreach for this lead.\n"
        f"Business: {name} | Industry: {industry} | Address: {address or 'unknown'} | "
        f"Rating: {rating or 'N/A'}★ | Has Website: {'yes' if has_website else 'no'}\n"
        f"{service_line}\n{pain_line}\n{proof_line}\n"
        f"Talk track: {talk_track}\n"
        f"Tone: {style} | Language: {'Indonesian' if is_id else 'English'} | Score: {score}/100\n\n"
        "Rules: reference specific pain points, mention case study outcome if provided, "
        "email body 100-150 words, WhatsApp 50-80 words with 1-2 emoji, Instagram 40-60 words, "
        "LinkedIn under 280 chars.\n\n"
        'Return ONLY valid JSON:\n'
        '{"email":{"subject":"...","body":"..."},"whatsapp":"...","instagram":"...",'
        '"linkedin":{"connectionNote":"..."},"coldCall":{"opening":"..."},'
        '"pitchAngle":"slug","proofPoint":"case study title or null"}'
    )

    result = await complete_json(
        [{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000,
        fallback_fn=lambda: _fallback_dict(name, industry, rating, your_service, language, brief, case_study, top_service),
    )

    if not result or not isinstance(result, dict):
        return _fallback(name, industry, rating, your_service, language, brief, case_study, top_service)

    return MarketingContent(
        email_subject=result.get("email", {}).get("subject", ""),
        email_body=result.get("email", {}).get("body", ""),
        whatsapp=result.get("whatsapp", ""),
        instagram=result.get("instagram", ""),
        linkedin_note=result.get("linkedin", {}).get("connectionNote", ""),
        cold_call_opening=result.get("coldCall", {}).get("opening", ""),
        pitch_angle=result.get("pitchAngle", "general"),
        proof_point=result.get("proofPoint"),
    )


def _fallback(
    name: str, industry: str, rating: Optional[str], service: str, language: str,
    brief: "Optional[SalesBrief]",
    case_study: "Optional[CaseStudyMatch]",
    top_service: "Optional[ServiceMatch]",
) -> MarketingContent:
    d = _fallback_dict(name, industry, rating, service, language, brief, case_study, top_service)
    return MarketingContent(
        email_subject=d["email"]["subject"],
        email_body=d["email"]["body"],
        whatsapp=d["whatsapp"],
        instagram=d["instagram"],
        linkedin_note=d["linkedin"]["connectionNote"],
        cold_call_opening=d["coldCall"]["opening"],
        pitch_angle=d["pitchAngle"],
        proof_point=d["proofPoint"],
    )


def _fallback_dict(
    name: str, industry: str, rating: Optional[str], service: str, language: str,
    brief: "Optional[SalesBrief]",
    case_study: "Optional[CaseStudyMatch]",
    top_service: "Optional[ServiceMatch]",
) -> dict:
    top_pain = brief.pain_points[0].title if brief and brief.pain_points else None
    proof = f"We recently {case_study.outcome.lower()}." if case_study else ""
    svc = top_service.service_name if top_service else service
    r_tag = f" with a {rating}-star rating" if rating and rating != "N/A" else ""
    angle = top_pain.lower().replace(" ", "-") if top_pain else "general"
    cs_title = case_study.title if case_study else None

    if language == "indonesian":
        pain_line = f"Satu hal yang langsung saya perhatikan: {top_pain.lower()}." if top_pain else ""
        return {
            "email": {
                "subject": f"Solusi untuk {name}" if not top_pain else f"Soal {top_pain.lower()} — {name}",
                "body": (f"Halo tim {name},\n\nSaya melihat bisnis Anda{r_tag.replace(' with a', ' dengan').replace('-star rating', ' bintang')} dan melihat peluang nyata.\n\n"
                         f"{pain_line}\n\n{proof}\n\nKami bisa membantu {name} dengan {svc}.\n\nAda waktu 15 menit?\n\nSalam,\n[Nama Anda]"),
            },
            "whatsapp": f"Halo {name}! {('Saya lihat ada kesempatan besar soal ' + top_pain.lower() + '.') if top_pain else ''} {proof} Boleh chat sebentar?",
            "instagram": f"Hi {name}! {('Peluang besar di ' + top_pain.lower() + ' 🔥') if top_pain else 'Bisnis keren!'} {proof} DM yuk! ✨",
            "linkedin": {"connectionNote": f"Halo, saya tertarik dengan {name}. Spesialisasi saya di {svc}. Mari connect!"},
            "coldCall": {"opening": f"Selamat pagi, boleh berbicara dengan pemilik {name}? Saya ingin berbagi bagaimana {svc} bisa membantu bisnis Anda."},
            "pitchAngle": angle, "proofPoint": cs_title,
        }

    pain_sub = f"Quick question about {top_pain.lower()} — {name}" if top_pain else f"Grow {name} with {svc}"
    pain_body = f"noticed {top_pain.lower()}" if top_pain else "a real growth opportunity"
    pain_wa = f"Noticed {top_pain.lower()}." if top_pain else "Spotted a big opportunity."
    pain_ig = f"Noticed {top_pain.lower()} could be a big win 🔥" if top_pain else "Love what you are building!"
    pain_li = f" has an opportunity around {top_pain.lower()}" if top_pain else ""
    pain_cc = f"a gap around {top_pain.lower()}" if top_pain else "a growth opportunity"

    return {
        "email": {
            "subject": pain_sub,
            "body": (f"Hi {name} team,\n\nI came across your business{r_tag} and {pain_body}.\n\n"
                     f"{proof}\n\nI'd love to show you how {svc} could help {name} achieve similar results.\n\n"
                     f"Would you have 15 minutes for a quick call?\n\nBest,\n[Your Name]"),
        },
        "whatsapp": f"Hi {name}! 👋 {pain_wa} {proof} Think we can help — quick chat? 🚀",
        "instagram": f"Hi {name}! {pain_ig} {proof} DM me! ✨",
        "linkedin": {"connectionNote": f"Hi, noticed {name}{pain_li}. I specialise in {svc}. Would love to connect!"},
        "coldCall": {"opening": f"Hi, may I speak with the owner of {name}? I found {pain_cc} I would love to walk you through."},
        "pitchAngle": angle, "proofPoint": cs_title,
    }
