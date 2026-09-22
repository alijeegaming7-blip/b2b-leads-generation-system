"""
Email scraper — extracts email addresses from business websites
Uses Playwright to visit the site and extract contact emails
"""
from __future__ import annotations
import asyncio
import logging
import re
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

logger = logging.getLogger(__name__)

EMAIL_REGEX = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'


async def scrape_email_from_website(url: str, timeout: int = 12) -> str:
    """
    Visit a business website and try to extract an email address.
    Returns the first valid email found, or empty string.
    """
    if not url or not url.startswith('http'):
        return ""

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            page = await browser.new_page()
            page.set_default_timeout(timeout * 1000)

            # Load main page
            try:
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(1500)
            except PWTimeoutError:
                await browser.close()
                return ""

            # Extract all text from page
            body_text = await page.evaluate("() => document.body?.innerText || ''")
            
            # Also check common contact page links
            contact_links = await page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links
                    .filter(a => /contact|about|team/i.test(a.textContent || a.href))
                    .map(a => a.href)
                    .filter(h => h.startsWith('http'))
                    .slice(0, 2);
            }""")

            emails = set()
            
            # Extract from main page
            for match in re.finditer(EMAIL_REGEX, body_text):
                email = match.group(0).lower()
                if _is_valid_business_email(email):
                    emails.add(email)
                    if len(emails) >= 3:
                        break

            # If no email found, try contact page
            if not emails and contact_links:
                for link in contact_links[:1]:  # Only try first contact link
                    try:
                        await page.goto(link, wait_until="domcontentloaded", timeout=8000)
                        await page.wait_for_timeout(1000)
                        contact_text = await page.evaluate("() => document.body?.innerText || ''")
                        for match in re.finditer(EMAIL_REGEX, contact_text):
                            email = match.group(0).lower()
                            if _is_valid_business_email(email):
                                emails.add(email)
                                if len(emails) >= 2:
                                    break
                    except Exception:
                        pass

            await browser.close()

            # Return best email (prefer info@, contact@, hello@ over personal names)
            if emails:
                sorted_emails = sorted(emails, key=_email_priority)
                return sorted_emails[0]

            return ""

    except Exception as exc:
        logger.debug(f"Email scrape failed for {url}: {exc}")
        return ""


def _is_valid_business_email(email: str) -> bool:
    """Filter out common spam/placeholder emails"""
    email = email.lower()
    
    # Exclude obvious spam/placeholder domains
    spam_domains = [
        'example.com', 'test.com', 'email.com', 'domain.com',
        'yoursite.com', 'yourdomain.com', 'sentry.io', 'wixpress.com',
        'facebook.com', 'gmail.com', 'yahoo.com', 'hotmail.com',  # Usually personal, not business
    ]
    
    for spam in spam_domains:
        if spam in email:
            return False
    
    # Exclude noreply, no-reply, do-not-reply
    if 'noreply' in email or 'no-reply' in email or 'donotreply' in email:
        return False
    
    # Must have proper format
    if email.count('@') != 1:
        return False
    
    # Must have domain with TLD
    if '.' not in email.split('@')[1]:
        return False
    
    return True


def _email_priority(email: str) -> int:
    """Lower score = higher priority"""
    email = email.lower()
    
    # Prefer business contact emails
    if email.startswith('info@'): return 0
    if email.startswith('contact@'): return 1
    if email.startswith('hello@'): return 2
    if email.startswith('sales@'): return 3
    if email.startswith('support@'): return 4
    
    # Deprioritize personal-looking emails
    if any(name in email for name in ['john', 'jane', 'admin', 'webmaster']):
        return 10
    
    return 5
