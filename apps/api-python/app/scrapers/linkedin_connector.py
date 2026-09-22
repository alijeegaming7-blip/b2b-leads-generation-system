"""
LinkedIn Sales Navigator connector with OAuth support.

Allows searching for companies and people on LinkedIn.
Requires OAuth authentication or API key.
"""
import aiohttp
from typing import List, Optional, Dict, Any
from .base_connector import BaseConnector, ConnectorResult
import logging

logger = logging.getLogger(__name__)


class LinkedInConnector(BaseConnector):
    """
    LinkedIn Sales Navigator connector.
    
    Note: LinkedIn restricts automated access heavily.
    This connector requires either:
    1. LinkedIn Sales Navigator subscription + OAuth token
    2. Third-party LinkedIn API service (e.g., Proxycurl, RapidAPI LinkedIn)
    """
    
    @property
    def name(self) -> str:
        return "linkedin"
    
    @property
    def display_name(self) -> str:
        return "LinkedIn Sales Navigator"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    @property
    def requires_oauth(self) -> bool:
        """This connector supports OAuth"""
        return True
    
    def get_oauth_config(self) -> Dict[str, str]:
        """
        Get OAuth configuration for LinkedIn.
        
        Returns:
            Dict with authorize_url, token_url, scopes
        """
        return {
            "authorize_url": "https://www.linkedin.com/oauth/v2/authorization",
            "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
            "scopes": ["r_basicprofile", "r_organization_social", "w_organization_social"],
            "client_id_env": "LINKEDIN_CLIENT_ID",
            "client_secret_env": "LINKEDIN_CLIENT_SECRET",
        }
    
    async def search(
        self, 
        query: str, 
        location: str,
        limit: int = 10,
        use_proxycurl: bool = True,
        **kwargs
    ) -> List[ConnectorResult]:
        """
        Search LinkedIn for companies.
        
        Args:
            query: Company industry or type
            location: Geographic location
            limit: Maximum results
            use_proxycurl: Use Proxycurl API (requires separate API key)
        
        Returns:
            List of ConnectorResult objects
        """
        if not self.api_key:
            raise ValueError("LinkedIn connector requires an API key (Proxycurl or RapidAPI)")
        
        results = []
        
        # Use Proxycurl API (most reliable LinkedIn data provider)
        if use_proxycurl:
            results = await self._search_via_proxycurl(query, location, limit)
        else:
            # Use direct LinkedIn API (restricted, may not work)
            results = await self._search_via_linkedin_api(query, location, limit)
        
        return results
    
    async def _search_via_proxycurl(
        self, 
        query: str, 
        location: str, 
        limit: int
    ) -> List[ConnectorResult]:
        """
        Search using Proxycurl API.
        
        Proxycurl: https://nubela.co/proxycurl/
        """
        url = "https://nubela.co/proxycurl/api/v2/search/company"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        params = {
            "query": query,
            "location": location,
            "page_size": min(limit, 100),
            "enrich_profiles": "enrich",  # Get full company data
        }
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error(f"Proxycurl API error {resp.status}: {error}")
                        return []
                    
                    data = await resp.json()
            
            for company in data.get("results", []):
                # Extract company details
                result = ConnectorResult(
                    name=company.get("name", ""),
                    phone=company.get("phone"),
                    email=None,  # LinkedIn doesn't provide direct emails
                    website=company.get("website"),
                    address=company.get("hq", {}).get("line_1"),
                    city=company.get("hq", {}).get("city"),
                    state=company.get("hq", {}).get("state"),
                    zip_code=company.get("hq", {}).get("postal_code"),
                    country=company.get("hq", {}).get("country"),
                    rating=None,
                    review_count=None,
                    category=query,
                    source=self.name,
                    raw_data={
                        "linkedin_url": company.get("linkedin_url"),
                        "company_size": company.get("company_size"),
                        "industry": company.get("industry"),
                        "specialties": company.get("specialties", []),
                        "employee_count": company.get("employee_count"),
                        "follower_count": company.get("follower_count"),
                        "description": company.get("description"),
                        "founded_year": company.get("founded_year"),
                        "social_media": {
                            "linkedin": company.get("linkedin_url"),
                            "facebook": company.get("facebook_url"),
                            "twitter": company.get("twitter_url"),
                        }
                    }
                )
                results.append(result)
        
        except Exception as e:
            logger.error(f"Proxycurl search failed: {e}")
        
        return results
    
    async def _search_via_linkedin_api(
        self, 
        query: str, 
        location: str, 
        limit: int
    ) -> List[ConnectorResult]:
        """
        Search using official LinkedIn API.
        
        Note: Very restricted, requires LinkedIn partnership.
        """
        # LinkedIn's official API is very limited
        # Most users will need Proxycurl or similar service
        logger.warning("Direct LinkedIn API search not fully implemented - use Proxycurl")
        return []
    
    async def enrich_company(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed company information from LinkedIn URL.
        
        Args:
            linkedin_url: LinkedIn company page URL
        
        Returns:
            Detailed company data
        """
        if not self.api_key:
            return None
        
        url = "https://nubela.co/proxycurl/api/linkedin/company"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"url": linkedin_url}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.error(f"LinkedIn enrichment failed: {e}")
        
        return None
