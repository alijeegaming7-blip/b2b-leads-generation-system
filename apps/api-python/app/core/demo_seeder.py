"""
Demo Seeder — pre-loads 30 real Pakistani business leads on first startup.
These leads come from a hardcoded dataset so the demo works immediately
without waiting for Google Maps scraping.

Contact info (phone, email, social) is blurred by the demo middleware.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# 30 real Pakistani business leads (Restaurant, Dental, Hotel categories)
DEMO_LEADS = [
    {"name":"Café Aylanto","address":"42-E/1, Main Boulevard, Gulberg III, Lahore","phone":"+92 42 3578 4000","email":"info@aylanto.com","website":"https://aylanto.com","rating":"4.5","review_count":3241,"category":"Restaurant","source":"google_maps","social_media":{"facebook":"https://facebook.com/aylantoofficial","instagram":"https://instagram.com/cafeaylanto"}},
    {"name":"Monal Restaurant","address":"Daman-e-Koh, Margalla Hills, Islamabad","phone":"+92 51 2896 001","email":"monal@monal.com.pk","website":"https://monal.com.pk","rating":"4.3","review_count":8921,"category":"Restaurant","source":"google_maps","social_media":{"facebook":"https://facebook.com/monalpk","instagram":"https://instagram.com/monalpk"}},
    {"name":"Kolachi Restaurant","address":"Do Darya, Phase 8, DHA, Karachi","phone":"+92 21 3530 2244","email":"info@kolachi.pk","website":"https://kolachi.pk","rating":"4.4","review_count":5632,"category":"Restaurant","source":"google_maps","social_media":{"facebook":"https://facebook.com/kolachirestaurant"}},
    {"name":"Salt'n Pepper","address":"25-A, Liberty Market, Gulberg III, Lahore","phone":"+92 42 3576 5050","email":"info@saltnpepper.pk","website":"https://saltnpepper.pk","rating":"4.2","review_count":4120,"category":"Restaurant","source":"google_maps","social_media":{"instagram":"https://instagram.com/saltnpepperpk"}},
    {"name":"Burning Brownie","address":"Plot 54-C, 26th Street, Phase 5, DHA, Karachi","phone":"+92 21 3584 4242","email":"hello@burningbrownie.com","website":"https://burningbrownie.com","rating":"4.6","review_count":2890,"category":"Restaurant","source":"google_maps","social_media":{"facebook":"https://facebook.com/burningbrowniepk","instagram":"https://instagram.com/burningbrowniepk","tiktok":"https://tiktok.com/@burningbrownie"}},
    {"name":"Savour Foods","address":"Jinnah Super Market, F-7 Markaz, Islamabad","phone":"+92 51 2654 321","email":"savourfoods@gmail.com","website":"","rating":"4.5","review_count":6710,"category":"Restaurant","source":"google_maps","social_media":{"facebook":"https://facebook.com/savourfoods"}},
    {"name":"Lord of the Drinks","address":"61-B, MM Alam Road, Gulberg, Lahore","phone":"+92 42 3570 0090","email":"info@lordofthedrinks.pk","website":"https://lordofthedrinks.pk","rating":"4.4","review_count":3450,"category":"Restaurant","source":"google_maps","social_media":{"instagram":"https://instagram.com/lordofthedrinkspk"}},
    {"name":"Lasania Restaurant","address":"112, Block N, Model Town, Lahore","phone":"+92 42 3516 2222","email":"lasania@lasania.com","website":"https://lasania.com","rating":"4.3","review_count":7820,"category":"Restaurant","source":"google_maps","social_media":{"facebook":"https://facebook.com/lasaniarestaurant"}},
    {"name":"Arizona Grill","address":"26th Street, Phase 5, DHA, Karachi","phone":"+92 21 3586 9090","email":"info@arizonagrill.pk","website":"https://arizonagrill.pk","rating":"4.2","review_count":2340,"category":"Restaurant","source":"google_maps","social_media":{"instagram":"https://instagram.com/arizonagrillpk"}},
    {"name":"Tuscany Courtyard","address":"16 C-1, MM Alam Road, Lahore","phone":"+92 42 3578 5858","email":"tuscany@tuscanycourtyard.com","website":"https://tuscanycourtyard.com","rating":"4.5","review_count":4560,"category":"Restaurant","source":"google_maps","social_media":{"facebook":"https://facebook.com/tuscanycourtyardlahore","instagram":"https://instagram.com/tuscanycourtyard"}},
    # Dental Clinics
    {"name":"Dental Aesthetics","address":"187 Y, Street 11, DHA Phase 3, Lahore","phone":"+92 303 2737773","email":"talk@dentalaesthetics.pk","website":"https://dentalaesthetics.pk","rating":"4.6","review_count":455,"category":"Dental Clinic","source":"google_maps","social_media":{"facebook":"https://facebook.com/dentalaestheticspk","instagram":"https://instagram.com/dentalaestheticspk","linkedin":"https://linkedin.com/company/dental-aesthetics123","youtube":"https://youtube.com/dentalaestheticspk","whatsapp":"https://wa.me/923218406474"}},
    {"name":"SmileOn Dental","address":"Shaukat Khanum Hospital Road, DHA, Lahore","phone":"+92 331 1066666","email":"info@smileondental.pk","website":"https://smileondental.pk","rating":"4.8","review_count":568,"category":"Dental Clinic","source":"google_maps","social_media":{"facebook":"https://facebook.com/smileondental","instagram":"https://instagram.com/smileondental"}},
    {"name":"Dental Clinic by Dr Bilal","address":"Wapda Town, Lahore","phone":"+92 331 6018700","email":"info@dentistdrbilal.com","website":"https://dentistdrbilal.com","rating":"4.9","review_count":263,"category":"Dental Clinic","source":"google_maps","social_media":{"instagram":"https://instagram.com/dentistinlahore"}},
    {"name":"Teeth and Smile Dental Clinic","address":"Block D, Model Town, Lahore","phone":"+92 327 7088881","email":"info@teethandsmile.pk","website":"https://teethandsmile.pk","rating":"4.7","review_count":312,"category":"Dental Clinic","source":"google_maps","social_media":{"facebook":"https://facebook.com/teethandsmile","instagram":"https://instagram.com/teethandsmile","linkedin":"https://linkedin.com/company/teethandsmile","youtube":"https://youtube.com/teethandsmile","tiktok":"https://tiktok.com/@teethandsmile","whatsapp":"https://wa.me/923277088881"}},
    {"name":"32 Dental Care","address":"Defence Road, Lahore","phone":"+92 331 4969588","email":"info@32dentalcare.pk","website":"https://32dentalcare.pk","rating":"4.8","review_count":189,"category":"Dental Clinic","source":"google_maps","social_media":{"facebook":"https://facebook.com/32dentalcare","instagram":"https://instagram.com/32dentalcare"}},
    # Hotels
    {"name":"Pearl Continental Hotel Lahore","address":"Shahrah-e-Quaid-e-Azam, Lahore","phone":"+92 42 111 505 505","email":"pclahore@pchotels.com","website":"https://pchotels.com","rating":"4.5","review_count":9820,"category":"Hotel","source":"google_maps","social_media":{"facebook":"https://facebook.com/pchotels","instagram":"https://instagram.com/pchotels","twitter":"https://twitter.com/pchotels"}},
    {"name":"Serena Hotel Islamabad","address":"Khayaban-e-Suharwardy, Islamabad","phone":"+92 51 111 133 133","email":"reservations@serena.com.pk","website":"https://serena.com.pk","rating":"4.6","review_count":7634,"category":"Hotel","source":"google_maps","social_media":{"facebook":"https://facebook.com/serenahotels","instagram":"https://instagram.com/serenahotels","twitter":"https://twitter.com/serenahotels"}},
    {"name":"Avari Towers Karachi","address":"Fatima Jinnah Road, Karachi","phone":"+92 21 111 282 274","email":"towers@avari.com","website":"https://avari.com","rating":"4.4","review_count":5410,"category":"Hotel","source":"google_maps","social_media":{"facebook":"https://facebook.com/avarihotels"}},
    {"name":"Marriott Hotel Islamabad","address":"Aga Khan Road, Shalimar 5, Islamabad","phone":"+92 51 282 7777","email":"info@marriottislamabad.com","website":"https://marriott.com","rating":"4.5","review_count":8901,"category":"Hotel","source":"google_maps","social_media":{"facebook":"https://facebook.com/islamabadmarriott","instagram":"https://instagram.com/islamabadmarriott"}},
    {"name":"Ramada by Wyndham Karachi","address":"Block 9, Clifton, Karachi","phone":"+92 21 3586 0271","email":"info@ramadakarachi.com","website":"https://ramadakarachi.com","rating":"4.2","review_count":3240,"category":"Hotel","source":"google_maps","social_media":{"facebook":"https://facebook.com/ramadakarachi"}},
    # Law Firms
    {"name":"Cornelius Lane & Mufti","address":"3 Mozang Road, Lahore","phone":"+92 42 3636 3400","email":"info@corneliuslane.com","website":"https://corneliuslane.com","rating":"4.7","review_count":89,"category":"Law Firm","source":"google_maps","social_media":{"linkedin":"https://linkedin.com/company/cornelius-lane-mufti"}},
    {"name":"Orr Dignam & Co","address":"Block 7-8, Clifton, Karachi","phone":"+92 21 3587 2400","email":"info@orrdignam.com","website":"https://orrdignam.com","rating":"4.8","review_count":67,"category":"Law Firm","source":"google_maps","social_media":{"linkedin":"https://linkedin.com/company/orr-dignam"}},
    # Salons/Spas
    {"name":"Nabila's Salon","address":"26-B, Khayaban-e-Ittehad, DHA Phase 6, Karachi","phone":"+92 21 3535 7590","email":"nabilas@nabila.net","website":"https://nabila.net","rating":"4.5","review_count":2340,"category":"Beauty Salon","source":"google_maps","social_media":{"facebook":"https://facebook.com/nabilasofficial","instagram":"https://instagram.com/nabilasofficial"}},
    {"name":"Depilex Beauty Clinic","address":"MM Alam Road, Gulberg, Lahore","phone":"+92 42 3578 8900","email":"info@depilex.com","website":"https://depilex.com","rating":"4.4","review_count":1890,"category":"Beauty Salon","source":"google_maps","social_media":{"facebook":"https://facebook.com/depilexpk","instagram":"https://instagram.com/depilexpk"}},
    # Real Estate
    {"name":"Zameen.com Office Lahore","address":"67-A, MM Alam Road, Lahore","phone":"+92 42 111 100 200","email":"support@zameen.com","website":"https://zameen.com","rating":"4.3","review_count":4560,"category":"Real Estate","source":"google_maps","social_media":{"facebook":"https://facebook.com/zameencom","twitter":"https://twitter.com/zameencom","linkedin":"https://linkedin.com/company/zameencom"}},
    {"name":"Al-Hafeez Builders","address":"Gulberg III, Lahore","phone":"+92 42 3577 5050","email":"info@alhafeezbuilders.com","website":"https://alhafeezbuilders.com","rating":"4.2","review_count":234,"category":"Real Estate","source":"google_maps","social_media":{"facebook":"https://facebook.com/alhafeezbuilders"}},
    # Gyms
    {"name":"Shapes Gym Karachi","address":"Phase 5, DHA, Karachi","phone":"+92 21 3584 5550","email":"info@shapesgym.pk","website":"https://shapesgym.pk","rating":"4.6","review_count":890,"category":"Gym","source":"google_maps","social_media":{"instagram":"https://instagram.com/shapesgympk","facebook":"https://facebook.com/shapesgym"}},
    {"name":"Fitness One Lahore","address":"Johar Town, Lahore","phone":"+92 42 3521 8080","email":"contact@fitnessone.pk","website":"https://fitnessone.pk","rating":"4.5","review_count":1230,"category":"Gym","source":"google_maps","social_media":{"facebook":"https://facebook.com/fitnessonepk","instagram":"https://instagram.com/fitnessonepk"}},
    # Pharmacies
    {"name":"Fazal Din's Pharma","address":"Ferozpur Road, Lahore","phone":"+92 42 3763 3880","email":"info@fazaldin.com","website":"https://fazaldin.com","rating":"4.4","review_count":3450,"category":"Pharmacy","source":"google_maps","social_media":{"facebook":"https://facebook.com/fazaldinspharma"}},
    {"name":"Sehat Medical Store","address":"Blue Area, Islamabad","phone":"+92 51 2273 600","email":"sehat@sehatpharma.pk","website":"https://sehatpharma.pk","rating":"4.3","review_count":567,"category":"Pharmacy","source":"google_maps","social_media":{"instagram":"https://instagram.com/sehatpharma"}},
]


async def seed_demo_leads(workspace_id: str, campaign_id: str) -> int:
    """
    Insert the 30 demo leads into the database.
    Returns number of leads inserted.
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.core.ids import new_id
        from app.models.lead import Lead
        from sqlalchemy import select, func

        async with AsyncSessionLocal() as db:
            # Check if already seeded
            count_result = await db.execute(
                select(func.count(Lead.id)).where(Lead.workspace_id == workspace_id)
            )
            existing = count_result.scalar() or 0
            if existing >= 30:
                logger.info(f"[demo_seeder] Already have {existing} leads, skipping seed")
                return 0

            inserted = 0
            for lead_data in DEMO_LEADS:
                lead = Lead(
                    id=new_id(),
                    name=lead_data["name"],
                    address=lead_data["address"],
                    phone=lead_data["phone"],
                    email=lead_data["email"],
                    website=lead_data.get("website", ""),
                    rating=lead_data.get("rating", ""),
                    review_count=lead_data.get("review_count", 0),
                    has_website=bool(lead_data.get("website")),
                    source=lead_data.get("source", "google_maps"),
                    category=lead_data.get("category", ""),
                    social_media=json.dumps(lead_data.get("social_media", {})),
                    score=75,
                    priority="HIGH",
                    pipeline_stage="DISCOVER",
                    crm_status="new",
                    ai_analysis=json.dumps({
                        "agent_id": "demo_seeder",
                        "issues_found": [
                            "No automated follow-up system for enquiries",
                            "Manual appointment booking via phone only",
                            "No AI chatbot for 24/7 customer support",
                        ]
                    }),
                    workspace_id=workspace_id,
                    campaign_id=campaign_id,
                )
                db.add(lead)
                inserted += 1

            await db.commit()
            logger.info(f"[demo_seeder] Seeded {inserted} demo leads")
            return inserted

    except Exception as e:
        logger.error(f"[demo_seeder] Failed to seed leads: {e}")
        return 0
