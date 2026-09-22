"""
Hunter.io connector for email finding and verification.

Hunter specializes in finding professional email addresses.
API: https://hunter.io/api-documentation
"""
import aiohttp
from typing import List, Optional, Dict, Any
from .base_connector import BaseConnector, ConnectorResult
import logging

logger = logging.getLogger(__name__)


class HunterConnector(BaseConnector):
    """
    Hunter.io email finder and verifier.
    
    Hunter finds email addresses associated with domains.
    """
    
    BASE_URL = "https://api.hunter.io/v2"
    
    @property
    def name(self) -> str:
        return "hunter"
    
    @property
    def display_name(self) -> str:
        return "Hunter.io Email Finder"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    async def search(
        self, 
        query: str, 
        location: str,
        limit: int = 10,
        **kwargs
    ) -> List[ConnectorResult]:
        """
        Hunter doesn't do company search, but can enrich domains with emails.
        This method searches domain directory.
        
        Args:
            query: Domain or company name
            location: Not used by Hunter
            limit: Maximum results
        
        Returns:
            List of ConnectorResult objects
        """
        # Hunter is best used for enrichment, not discovery
        # Return empty for now
        logger.info("Hunter.io is better used for email enrichment, not discovery")
        return []
    
    async def find_emails_for_domain(
        self, 
        domain: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find all email addresses associated with a domain.
        
        Args:
            domain: Company domain (e.g., "stripe.com")
            limit: Maximum emails to return
        
        Returns:
            List of email data dicts
        """
        if not self.api_key:
            raise ValueError("Hunter connector requires an API key")
        
        url = f"{self.BASE_URL}/domain-search"
        params = {
            "domain": domain,
            "api_key": self.api_key,
            "limit": min(limit, 100),
        }
        
        emails = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error(f"Hunter API error {resp.status}: {error}")
                        return []
                    
                    data = await resp.json()
            
            for email_data in data.get("data", {}).get("emails", []):
                emails.append({
                    "email": email_data.get("value"),
                    "first_name": email_data.get("first_name"),
                    "last_name": email_data.get("last_name"),
                    "position": email_data.get("position"),
                    "department": email_data.get("department"),
                    "confidence": email_data.get("confidence"),
                    "linkedin": email_data.get("linkedin"),
                    "twitter": email_data.get("twitter"),
                })
        
        except Exception as e:
            logger.error(f"Hunter domain search failed: {e}")
        
        return emails
    
    async def find_email(
        self,
        domain: str,
        first_name: str,
        last_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find email address for a specific person.
        
        Args:
            domain: Company domain
            first_name: Person's first name
            last_name: Person's last name
        
        Returns:
            Email data dict with confidence score
        """
        if not self.api_key:
            raise ValueError("Hunter connector requires an API key")
        
        url = f"{self.BASE_URL}/email-finder"
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": self.api_key,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return None
                    
                    data = await resp.json()
            
            email_data = data.get("data", {})
            return {
                "email": email_data.get("email"),
                "score": email_data.get("score"),
                "first_name": email_data.get("first_name"),
                "last_name": email_data.get("last_name"),
                "position": email_data.get("position"),
            }
        
        except Exception as e:
            logger.error(f"Hunter email finder failed: {e}")
        
        return None
    
    async def verify_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Verify if an email address is valid and deliverable.
        
        Args:
            email: Email address to verify
        
        Returns:
            Verification result with status and score
        """
        if not self.api_key:
            raise ValueError("Hunter connector requires an API key")
        
        url = f"{self.BASE_URL}/email-verifier"
        params = {
            "email": email,
            "api_key": self.api_key,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return None
                    
                    data = await resp.json()
            
            result = data.get("data", {})
            return {
                "email": result.get("email"),
                "status": result.get("status"),  # valid, invalid, accept_all, unknown
                "score": result.get("score"),  # 0-100
                "result": result.get("result"),  # deliverable, undeliverable, risky
                "mx_records": result.get("mx_records"),
                "smtp_server": result.get("smtp_server"),
            }
        
        except Exception as e:
            logger.error(f"Hunter email verification failed: {e}")
        
        return None
    
    async def get_domain_info(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get email pattern and company info for a domain.
        
        Args:
            domain: Company domain
        
        Returns:
            Domain information including email pattern
        """
        if not self.api_key:
            raise ValueError("Hunter connector requires an API key")
        
        url = f"{self.BASE_URL}/domain-search"
        params = {
            "domain": domain,
            "api_key": self.api_key,
            "limit": 1,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return None
                    
                    data = await resp.json()
            
            domain_data = data.get("data", {})
            return {
                "domain": domain_data.get("domain"),
                "organization": domain_data.get("organization"),
                "email_pattern": domain_data.get("pattern"),  # e.g., "{first}.{last}"
                "total_emails": domain_data.get("total"),
                "social_media": {
                    "twitter": domain_data.get("twitter"),
                    "facebook": domain_data.get("facebook"),
                    "linkedin": domain_data.get("linkedin"),
                }
            }
        
        except Exception as e:
            logger.error(f"Hunter domain info failed: {e}")
        
        return None
