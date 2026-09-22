"""Google Maps scraper using Playwright (sync, runs in thread pool)."""
from __future__ import annotations
import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from playwright.sync_api import sync_playwright, Page

logger = logging.getLogger(__name__)


@dataclass
class ScrapedBusiness:
    name: str
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    rating: str = "N/A"
    review_count: Optional[int] = None
    has_website: bool = False
    reference_link: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    source: str = "google_maps"


def _extract_lat_lng(url: str) -> tuple[Optional[float], Optional[float]]:
    m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    if m: return float(m.group(1)), float(m.group(2))
    m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if m: return float(m.group(1)), float(m.group(2))
    return None, None


def _scrape_sync(query: str, max_results: int) -> list[dict]:
    safe_query = re.sub(r'[\x00-\x1f<>"\'`]', "", query)[:200]
    results: list[dict] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-blink-features=AutomationControlled"])
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"})
            page.set_viewport_size({"width": 1280, "height": 800})

            encoded = re.sub(r"[^a-zA-Z0-9 \-.,]", "", safe_query).replace(" ", "+")
            page.goto(f"https://www.google.com/maps/search/{encoded}/", wait_until="domcontentloaded", timeout=45000)
            try:
                page.locator('button:has-text("Accept all"), button:has-text("Accept")').first.click(timeout=3000)
            except Exception:
                pass
            page.wait_for_timeout(2500)
            try:
                page.wait_for_selector('[role="feed"], .m6QErb, .Nv2PK', timeout=15000)
            except Exception:
                pass

            # Scroll to load more results
            feed_sel = '[role="feed"], .m6QErb'
            prev, stale = 0, 0
            for _ in range(20):
                page.evaluate(f"""() => {{ const el = document.querySelector('{feed_sel}'); if(el) el.scrollTop += 600; else window.scrollBy(0,600); }}""")
                page.wait_for_timeout(800)
                count = page.evaluate("() => document.querySelectorAll('.Nv2PK, [data-result-index]').length")
                if count >= max_results: break
                ended = page.evaluate("() => !!document.querySelector('[class*=\"HlvSq\"]') || !!document.querySelector('[aria-label*=\"end of list\" i]')")
                if ended: break
                stale = stale + 1 if count == prev else 0
                if stale >= 4: break
                prev = count

            raw_cards = page.eval_on_selector_all(".Nv2PK, [data-result-index]", r"""cards => cards.map(card => {
                let name = '';
                for (const sel of ['.qBF1Pd','.fontHeadlineSmall','[class*="fontHeadline"]','h3','[role="heading"]']) {
                    const el = card.querySelector(sel); if(el?.textContent?.trim()){name=el.textContent.trim();break;}
                }
                if(!name) return null;

                let rating='',reviewCount=null,address='',phone='',website='',refLink='';
                for(const sel of ['[aria-label*="star" i]','[aria-label*="rating" i]']){
                    const el=card.querySelector(sel);if(!el)continue;
                    const lbl=el.getAttribute('aria-label')||'';
                    const rm=lbl.match(/([\d.]+)\s*star/i);const rv=lbl.match(/([\d,]+)\s*review/i);
                    if(rm)rating=rm[1];if(rv)reviewCount=parseInt(rv[1].replace(/,/g,''),10);if(rating)break;
                }
                if(!rating){const rEl=card.querySelector('.MW4etd');if(rEl?.textContent)rating=rEl.textContent.trim();}

                // Extract phone from tel: href first (most reliable)
                const telLink = card.querySelector('a[href^="tel:"]');
                if(telLink) phone = telLink.href.replace('tel:','').replace(/%2B/gi,'+').trim();

                const frags=[];card.querySelectorAll('.W4Efsd span,.W4Efsd div').forEach(el=>{
                    if(el.childElementCount>2)return;const t=el.textContent?.trim()||'';
                    if(!t||t==='·'||t.length<2)return;if(/^\(\d[\d,]+\)$/.test(t))return;
                    if(/^(Open|Closed|Opens|Closes)/i.test(t))return;frags.push(t);
                });
                const unique=[...new Set(frags)];
                for(const t of unique){
                    const cleaned = t.replace(/^[·•\s\-\u00B7]+/, '').trim();
                    const digits = cleaned.replace(/\D/g,'');
                    if(!phone && digits.length >= 7 && digits.length <= 15){
                        const hasPlus = cleaned.startsWith('+') || cleaned.startsWith('0');
                        const looksLikePhone = hasPlus || /^\(?\d[\d\s\-\.\(\)]{5,14}\d$/.test(cleaned);
                        if(looksLikePhone && !/^\d{4,5}$/.test(digits)){ phone = cleaned; continue; }
                    }
                    if(!address && cleaned.length > 6){
                        const la = /\d{1,5}\s+[A-Za-z]/.test(cleaned) ||
                                   /\b(St|Ave|Rd|Blvd|Street|Avenue|Road|Block|Sector|Phase|Plot|House|DHA|Clifton|Gulshan|Gulberg|Defence|Bahria|North Nazimabad|Federal B|F-\d|G-\d|I-\d|H-\d|E-\d)\b/i.test(cleaned);
                        const lr = /^[\d.]+$/.test(cleaned) || /^\d+,\d+$/.test(cleaned);
                        if(la && !lr) address = cleaned;
                    }
                }
                for(const a of card.querySelectorAll('a[href]')){
                    const href=a.href||'';
                    if(href.includes('google.com/maps/place')&&!refLink)refLink=href;
                    else if(!website&&/^https?:\/\//.test(href)&&!href.includes('google.com'))website=href;
                }
                return {name,address,phone,website,rating:rating||'N/A',reviewCount,hasWebsite:!!website,refLink};
            }).filter(c=>c&&c.name.length>1)""")

            # ── Phase 2: Click into each listing for full contact data ──────
            # Google Maps detail page has phone, website, email visible
            # For cards missing phone or website, click to get detail
            listing_els = page.query_selector_all(".Nv2PK, [data-result-index]")
            
            for idx, card in enumerate(raw_cards[:max_results]):
                # Skip if already has both phone and website
                if card.get("phone") and card.get("website"):
                    continue
                # Only click first 8 cards to avoid timeout
                if idx >= 8:
                    break
                try:
                    if idx < len(listing_els):
                        listing_els[idx].click()
                        page.wait_for_timeout(2000)
                        
                        # Extract from detail panel
                        detail = page.evaluate(r"""() => {
                            const result = {phone: '', website: '', email: ''};
                            
                            // Phone: look for tel: link or phone aria-label
                            const telA = document.querySelector('a[href^="tel:"]');
                            if (telA) result.phone = telA.href.replace('tel:', '').replace(/%2B/gi, '+').trim();
                            if (!result.phone) {
                                const phBtn = document.querySelector('[data-tooltip="Copy phone number"], [aria-label*="Phone" i]');
                                if (phBtn) result.phone = (phBtn.getAttribute('aria-label') || phBtn.textContent || '').replace(/[^0-9+\-\s()]/g, '').trim();
                            }
                            
                            // Website: external link button
                            const webLinks = Array.from(document.querySelectorAll('a[href]')).filter(a => 
                                /^https?:\/\//.test(a.href) && 
                                !a.href.includes('google.com') && 
                                !a.href.includes('goo.gl') &&
                                a.href.length > 10
                            );
                            if (webLinks.length > 0) result.website = webLinks[0].href;
                            
                            // Email from page text
                            const pageText = document.body.innerText || '';
                            const emailMatch = pageText.match(/[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/);
                            if (emailMatch) result.email = emailMatch[0].toLowerCase();
                            
                            return result;
                        }""")
                        
                        # Update card with detail data
                        if detail.get("phone") and not card.get("phone"):
                            raw_cards[idx]["phone"] = detail["phone"]
                        if detail.get("website") and not card.get("website"):
                            raw_cards[idx]["website"] = detail["website"]
                            raw_cards[idx]["hasWebsite"] = True
                        if detail.get("email") and not raw_cards[idx].get("email"):
                            raw_cards[idx]["email"] = detail["email"]
                        
                        # Go back to list
                        page.go_back(wait_until="domcontentloaded", timeout=8000)
                        page.wait_for_timeout(800)
                        # Re-query listing elements after navigation
                        listing_els = page.query_selector_all(".Nv2PK, [data-result-index]")
                        
                except Exception as detail_exc:
                    logger.debug(f"Detail click failed for card {idx}: {detail_exc}")
                    try:
                        page.go_back(wait_until="domcontentloaded", timeout=5000)
                        page.wait_for_timeout(500)
                        listing_els = page.query_selector_all(".Nv2PK, [data-result-index]")
                    except Exception:
                        pass

            for card in raw_cards[:max_results]:
                lat, lng = _extract_lat_lng(card.get("refLink", ""))
                raw_phone = card.get("phone", "") or ""
                phone_clean = re.sub(r'[^\d\+\-\(\)\s]', '', raw_phone).strip()
                phone_clean = re.sub(r'^[\s\.\-]+', '', phone_clean).strip()
                if phone_clean and len(re.sub(r'\D', '', phone_clean)) < 6:
                    phone_clean = ""
                raw_addr = card.get("address", "") or ""
                addr_clean = re.sub(r'^[\s·\-\u00B7]+', '', raw_addr).strip()
                # Don't use "Closes X PM" as address
                if re.search(r'(Closes|Opens|Open now|Closed)', addr_clean, re.I):
                    addr_clean = ""

                results.append({
                    "name":           card["name"].strip(),
                    "address":        addr_clean,
                    "phone":          phone_clean,
                    "email":          card.get("email", "") or "",
                    "website":        card.get("website", ""),
                    "rating":         card.get("rating", "N/A"),
                    "review_count":   card.get("reviewCount"),
                    "has_website":    card.get("hasWebsite", False),
                    "reference_link": card.get("refLink", ""),
                    "lat": lat, "lng": lng,
                    "source": "google_maps",
                })
            browser.close()
    except Exception as exc:
        logger.error(f"Google Maps scrape failed for '{query}': {exc}")

    return results


async def scrape(query: str, max_results: int = 20) -> list[ScrapedBusiness]:
    raw = await asyncio.to_thread(_scrape_sync, query, max_results)
    return [ScrapedBusiness(**r) for r in raw]


async def enrich_email(website_url: str) -> str:
    """Visit a business site to try extracting an email address."""
    if not website_url:
        return ""

    def _sync() -> str:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                page = browser.new_page()
                page.goto(website_url, wait_until="domcontentloaded", timeout=12000)
                body = page.evaluate("() => document.body?.innerText || ''")
                browser.close()
                m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", body)
                return m.group(0) if m else ""
        except Exception:
            return ""

    return await asyncio.to_thread(_sync)
