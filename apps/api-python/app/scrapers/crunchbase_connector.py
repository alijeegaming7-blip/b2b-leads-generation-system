"""
Crunchbase connector for startup/company data.

API: https://data.crunchbase.com/docs
"""
import aiohttp
from typing import List, Optional, Dict, Any
from .base_connector import BaseConnector, ConnectorResult
import logging

logger = logging.getLogger(__name__)


class CrunchbaseConnector(BaseConnector):
    """Crunchbase API for company and funding data"""
    
    BASE_URL = "https://api.crunchbase.com/api/v4"
    
    @property
    def name(self) -> str:
        return "crunchbase"
    
    @property
    def display_name(self) -> str:
        return "Crunchbase"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    async def search(self, query: str, location: str, limit: int = 10, **kwargs) -> List[ConnectorResult]:
        """Search Crunchbase for organizations"""
        if not self.api_key:
            raise ValueError("Crunchbase requires API key")
        
        url = f"{self.BASE_URL}/searches/organizations"
        headers = {"X-cb-user-key": self.api_key}
        
        payload = {
            "field_ids": ["name", "website", "location_identifiers", "short_description", "linkedin"],
            "query": [{"type": "predicate", "field_id": "name", "operator_id": "includes", "values": [query]}],
            "limit": limit
        }
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error(f"Crunchbase API error: {error}")
                        return []
                    
                    data = await resp.json()
            
            for org in data.get("entities", []):
                props = org.get("properties", {})
                result = ConnectorResult(
                    name=props.get("name", ""),
                    phone=None,
                    email=None,
                    website=props.get("website"),
                    address=None,
                    city=None,
                    state=None,
                    zip_code=None,
                    country=None,
                    rating=None,
                    review_count=None,
                    category=query,
                    source=self.name,
                    raw_data={
                        "crunchbase_url": f"https://www.crunchbase.com/organization/{org.get('uuid')}",
                        "description": props.get("short_description"),
                        "linkedin": props.get("linkedin", {}).get("value"),
                        "location": props.get("location_identifiers"),
                    }
                )
                results.append(result)
        
        except Exception as e:
            logger.error(f"Crunchbase search failed: {e}")
        
        return results
