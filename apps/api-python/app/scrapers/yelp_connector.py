"""
Yelp Fusion API connector.

Requires Yelp API key from: https://www.yelp.com/developers
"""
import aiohttp
from typing import List, Optional, Dict, Any
from .base_connector import BaseConnector, ConnectorResult


class YelpConnector(BaseConnector):
    """Yelp Fusion API connector for business search"""
    
    BASE_URL = "https://api.yelp.com/v3"
    
    @property
    def name(self) -> str:
        return "yelp"
    
    @property
    def display_name(self) -> str:
        return "Yelp"
    
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
        Search Yelp for businesses.
        
        Args:
            query: Business category (e.g., "restaurant", "dentist")
            location: Geographic location (e.g., "New York, NY")
            limit: Maximum results (max 50 per Yelp API)
        
        Returns:
            List of ConnectorResult objects
        """
        if not self.api_key:
            raise ValueError("Yelp connector requires an API key")
        
        # Yelp API search endpoint
        url = f"{self.BASE_URL}/businesses/search"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "term": query,
            "location": location,
            "limit": min(limit, 50),  # Yelp max is 50
            "sort_by": "rating",  # best_match, rating, review_count, distance
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Yelp API error {resp.status}: {error_text}")
                
                data = await resp.json()
        
        results = []
        for biz in data.get("businesses", []):
            # Parse location
            loc = biz.get("location", {})
            address_parts = loc.get("display_address", [])
            full_address = ", ".join(address_parts) if address_parts else ""
            
            # Phone formatting
            phone = biz.get("phone") or biz.get("display_phone")
            
            result = ConnectorResult(
                name=biz.get("name", ""),
                phone=phone,
                email=None,  # Yelp API doesn't provide emails
                website=biz.get("url"),  # Yelp page URL
                address=full_address,
                city=loc.get("city"),
                state=loc.get("state"),
                zip_code=loc.get("zip_code"),
                country=loc.get("country"),
                rating=float(biz.get("rating", 0)) if biz.get("rating") else None,
                review_count=biz.get("review_count"),
                category=query,
                source=self.name,
                raw_data={
                    "yelp_id": biz.get("id"),
                    "yelp_url": biz.get("url"),
                    "is_closed": biz.get("is_closed", False),
                    "categories": [cat.get("title") for cat in biz.get("categories", [])],
                    "coordinates": biz.get("coordinates", {}),
                    "price": biz.get("price"),  # $, $$, $$$, $$$$
                    "transactions": biz.get("transactions", []),  # pickup, delivery, restaurant_reservation
                }
            )
            results.append(result)
        
        return results
    
    async def get_business_details(self, yelp_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific Yelp business.
        
        Args:
            yelp_id: Yelp business ID
        
        Returns:
            Detailed business information including hours, photos, etc.
        """
        if not self.api_key:
            raise ValueError("Yelp connector requires an API key")
        
        url = f"{self.BASE_URL}/businesses/{yelp_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
