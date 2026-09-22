"""
Apollo.io connector for B2B lead generation.

Apollo provides company and contact data with emails.
API: https://apolloio.github.io/apollo-api-docs/
"""
import aiohttp
from typing import List, Optional, Dict, Any
from .base_connector import BaseConnector, ConnectorResult
import logging

logger = logging.getLogger(__name__)


class ApolloConnector(BaseConnector):
    """
    Apollo.io connector for finding companies and contacts.
    
    Apollo provides verified emails, phone numbers, and social profiles.
    """
    
    BASE_URL = "https://api.apollo.io/v1"
    
    @property
    def name(self) -> str:
        return "apollo"
    
    @property
    def display_name(self) -> str:
        return "Apollo.io"
    
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
        Search Apollo for organizations matching query.
        
        Args:
            query: Industry or company type
            location: Geographic location
            limit: Maximum results (max 100 per API call)
        
        Returns:
            List of ConnectorResult objects
        """
        if not self.api_key:
            raise ValueError("Apollo connector requires an API key")
        
        url = f"{self.BASE_URL}/mixed_companies/search"
        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
        
        payload = {
            "q_keywords": query,
            "organization_locations": [location],
            "page": 1,
            "per_page": min(limit, 100),
        }
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error(f"Apollo API error {resp.status}: {error}")
                        return []
                    
                    data = await resp.json()
            
            for org in data.get("organizations", []):
                # Extract organization data
                result = ConnectorResult(
                    name=org.get("name", ""),
                    phone=org.get("phone"),
                    email=None,  # Organization-level email not in search results
                    website=org.get("website_url"),
                    address=org.get("street_address"),
                    city=org.get("city"),
                    state=org.get("state"),
                    zip_code=org.get("postal_code"),
                    country=org.get("country"),
                    rating=None,
                    review_count=None,
                    category=query,
                    source=self.name,
                    raw_data={
                        "apollo_id": org.get("id"),
                        "industry": org.get("industry"),
                        "employee_count": org.get("estimated_num_employees"),
                        "annual_revenue": org.get("annual_revenue"),
                        "founded_year": org.get("founded_year"),
                        "description": org.get("short_description"),
                        "social_media": {
                            "linkedin": org.get("linkedin_url"),
                            "facebook": org.get("facebook_url"),
                            "twitter": org.get("twitter_url"),
                        },
                        "technologies": org.get("technologies", []),
                        "keywords": org.get("keywords", []),
                    }
                )
                results.append(result)
        
        except Exception as e:
            logger.error(f"Apollo search failed: {e}")
        
        return results
    
    async def search_people(
        self,
        company_name: Optional[str] = None,
        job_titles: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for people/contacts at companies.
        
        Args:
            company_name: Filter by company
            job_titles: Filter by job titles (e.g., ["CEO", "Founder"])
            location: Geographic location
            limit: Maximum results
        
        Returns:
            List of contact dictionaries with emails
        """
        if not self.api_key:
            raise ValueError("Apollo connector requires an API key")
        
        url = f"{self.BASE_URL}/mixed_people/search"
        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
        
        payload = {
            "page": 1,
            "per_page": min(limit, 100),
        }
        
        if company_name:
            payload["organization_names"] = [company_name]
        if job_titles:
            payload["person_titles"] = job_titles
        if location:
            payload["person_locations"] = [location]
        
        contacts = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        return []
                    
                    data = await resp.json()
            
            for person in data.get("people", []):
                contact = {
                    "name": person.get("name"),
                    "first_name": person.get("first_name"),
                    "last_name": person.get("last_name"),
                    "email": person.get("email"),
                    "phone": person.get("phone_numbers", [{}])[0].get("raw_number") if person.get("phone_numbers") else None,
                    "title": person.get("title"),
                    "company": person.get("organization", {}).get("name"),
                    "linkedin": person.get("linkedin_url"),
                    "twitter": person.get("twitter_url"),
                }
                contacts.append(contact)
        
        except Exception as e:
            logger.error(f"Apollo people search failed: {e}")
        
        return contacts
    
    async def enrich_organization(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed organization data by domain.
        
        Args:
            domain: Company website domain
        
        Returns:
            Detailed organization data
        """
        if not self.api_key:
            return None
        
        url = f"{self.BASE_URL}/organizations/enrich"
        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
        params = {"domain": domain}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("organization")
        except Exception as e:
            logger.error(f"Apollo enrichment failed: {e}")
        
        return None
