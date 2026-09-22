"""
Clearbit connector for company enrichment.

API: https://clearbit.com/docs
"""
import aiohttp
from typing import List, Optional, Dict, Any
from .base_connector import BaseConnector, ConnectorResult
import logging

logger = logging.getLogger(__name__)


class ClearbitConnector(BaseConnector):
    """Clearbit enrichment API for company data"""
    
    BASE_URL = "https://company.clearbit.com/v2"
    
    @property
    def name(self) -> str:
        return "clearbit"
    
    @property
    def display_name(self) -> str:
        return "Clearbit"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    async def search(self, query: str, location: str, limit: int = 10, **kwargs) -> List[ConnectorResult]:
        """Clearbit doesn't have search, only enrichment"""
        return []
    
    async def enrich_company(self, domain: str) -> Optional[Dict[str, Any]]:
        """Enrich company data by domain"""
        if not self.api_key:
            raise ValueError("Clearbit requires API key")
        
        url = f"{self.BASE_URL}/companies/find"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"domain": domain}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.error(f"Clearbit enrichment failed: {e}")
        
        return None
