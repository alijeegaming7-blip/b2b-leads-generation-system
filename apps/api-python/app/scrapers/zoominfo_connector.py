"""
ZoomInfo connector stub.

ZoomInfo requires enterprise contract and custom API access.
This is a placeholder for future integration.
"""
from typing import List
from .base_connector import BaseConnector, ConnectorResult


class ZoomInfoConnector(BaseConnector):
    """ZoomInfo enterprise connector (requires custom API access)"""
    
    @property
    def name(self) -> str:
        return "zoominfo"
    
    @property
    def display_name(self) -> str:
        return "ZoomInfo (Enterprise)"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    async def search(self, query: str, location: str, limit: int = 10, **kwargs) -> List[ConnectorResult]:
        """ZoomInfo requires enterprise contract"""
        raise NotImplementedError("ZoomInfo requires enterprise API access. Contact ZoomInfo sales.")
