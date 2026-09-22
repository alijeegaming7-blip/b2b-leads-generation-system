"""
Demo Mode router — exposes demo status to frontend.
"""
from fastapi import APIRouter
from app.core.demo import get_config, demo_status_payload, is_demo

router = APIRouter(prefix="/demo", tags=["Demo"])


@router.get("/status")
async def demo_status():
    """
    Frontend calls this on load to know if demo mode is active.
    Returns demo config including buy link and upgrade message.
    """
    cfg = get_config()
    return {
        "demo_mode":   cfg.get("demo_mode", False),
        "buy_link":    cfg.get("demo_buy_link", ""),
        "demo_price":  cfg.get("demo_price", "$500"),
        "seller_name": cfg.get("demo_contact_name", ""),
        "upgrade_msg": (
            "🔒 Contact details are hidden in Demo Mode. "
            "Purchase the full system to unlock phone numbers, "
            "emails, and all social media profiles for every lead."
        ) if cfg.get("demo_mode") else "",
    }
