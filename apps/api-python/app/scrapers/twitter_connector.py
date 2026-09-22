"""
Twitter/X connector for business accounts.

Uses Twitter API v2 for searching business profiles.
"""
import aiohttp
from typing import List, Optional, Dict, Any
from .base_connector import BaseConnector, ConnectorResult
import logging

logger = logging.getLogger(__name__)


class TwitterConnector(BaseConnector):
    """Twitter/X API connector"""
    
    BASE_URL = "https://api.twitter.com/2"
    
    @property
    def name(self) -> str:
        return "twitter"
    
    @property
    def display_name(self) -> str:
        return "Twitter/X Business"
    
    @property
    def requires_api_key(self) -> bool:
        return True  # Bearer token
    
    async def search(self, query: str, location: str, limit: int = 10, **kwargs) -> List[ConnectorResult]:
        """Search Twitter for business accounts"""
        if not self.api_key:
            raise ValueError("Twitter requires API Bearer token")
        
        url = f"{self.BASE_URL}/users/search"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "query": f"{query} {location}",
            "max_results": min(limit, 100),
            "user.fields": "description,location,url,public_metrics"
        }
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error(f"Twitter API error: {error}")
                        return []
                    
                    data = await resp.json()
            
            for user in data.get("data", []):
                result = ConnectorResult(
                    name=user.get("name", ""),
                    phone=None,
                    email=None,
                    website=user.get("url"),
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
                        "twitter_handle": f"@{user.get('username')}",
                        "twitter_url": f"https://twitter.com/{user.get('username')}",
                        "description": user.get("description"),
                        "followers": user.get("public_metrics", {}).get("followers_count"),
                        "location": user.get("location"),
                    }
                )
                results.append(result)
        
        except Exception as e:
            logger.error(f"Twitter search failed: {e}")
        
        return results
