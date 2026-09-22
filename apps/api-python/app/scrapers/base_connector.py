"""
Base connector interface for multi-source lead scraping.

All connectors must implement this interface to work with the agent system.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ConnectorResult:
    """Standardized result from any connector"""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    category: Optional[str] = None
    source: str = "unknown"  # Which connector found this
    raw_data: Optional[Dict[str, Any]] = None  # Original data for debugging


class BaseConnector(ABC):
    """
    Base class for all lead scraping connectors.
    
    Each connector (Google Maps, Yelp, Yellow Pages, Facebook) implements this.
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize connector with optional API key and configuration.
        
        Args:
            api_key: API key for services that require authentication
            config: Additional configuration (rate limits, proxies, etc.)
        """
        self.api_key = api_key
        self.config = config or {}
        self._enabled = True
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Connector name (e.g., 'google_maps', 'yelp')"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'Google Maps', 'Yelp')"""
        pass
    
    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Whether this connector requires an API key"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        location: str,
        limit: int = 10,
        **kwargs
    ) -> List[ConnectorResult]:
        """
        Search for businesses matching query in location.
        
        Args:
            query: Business type/category (e.g., "restaurant", "dental clinic")
            location: Geographic location (e.g., "New York, USA")
            limit: Maximum number of results to return
            **kwargs: Additional connector-specific parameters
        
        Returns:
            List of ConnectorResult objects
        """
        pass
    
    def enable(self):
        """Enable this connector"""
        self._enabled = True
    
    def disable(self):
        """Disable this connector"""
        self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        """Check if connector is enabled"""
        return self._enabled
    
    def validate_config(self) -> "tuple[bool, Optional[str]]":
        """
        Validate connector configuration.

        Returns:
            (is_valid, error_message)
        """
        if self.requires_api_key and not self.api_key:
            return False, f"{self.display_name} requires an API key"
        return True, None


class ConnectorManager:
    """
    Manages multiple connectors and coordinates searches across them.
    """
    
    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
    
    def register(self, connector: BaseConnector):
        """Register a connector"""
        self._connectors[connector.name] = connector
    
    def unregister(self, connector_name: str):
        """Unregister a connector"""
        if connector_name in self._connectors:
            del self._connectors[connector_name]
    
    def get_connector(self, name: str) -> Optional[BaseConnector]:
        """Get connector by name"""
        return self._connectors.get(name)
    
    def list_connectors(self) -> List[Dict[str, Any]]:
        """List all registered connectors"""
        return [
            {
                "name": c.name,
                "display_name": c.display_name,
                "requires_api_key": c.requires_api_key,
                "is_enabled": c.is_enabled,
            }
            for c in self._connectors.values()
        ]
    
    async def search_all(
        self,
        query: str,
        location: str,
        limit_per_connector: int = 10,
        only_enabled: bool = True
    ) -> Dict[str, List[ConnectorResult]]:
        """
        Search across all connectors in parallel.
        
        Args:
            query: Business type/category
            location: Geographic location
            limit_per_connector: Max results per connector
            only_enabled: Only search enabled connectors
        
        Returns:
            Dict mapping connector name to results
        """
        results = {}
        
        for name, connector in self._connectors.items():
            if only_enabled and not connector.is_enabled:
                continue
            
            try:
                connector_results = await connector.search(query, location, limit_per_connector)
                results[name] = connector_results
            except Exception as e:
                # Log error but don't fail entire search
                print(f"[{name}] Error: {e}")
                results[name] = []
        
        return results
    
    async def search_with_fallback(
        self,
        query: str,
        location: str,
        limit: int = 10,
        priority_order: Optional[List[str]] = None
    ) -> List[ConnectorResult]:
        """
        Search connectors in priority order, falling back if needed.
        
        Only searches ENABLED connectors.
        
        Args:
            query: Business type/category
            location: Geographic location
            limit: Total number of results needed
            priority_order: Connector names in priority order
        
        Returns:
            Combined results from connectors
        """
        if priority_order is None:
            # Default priority: use all enabled connectors
            priority_order = [name for name, conn in self._connectors.items() if conn.is_enabled]
        else:
            # Filter priority list to only enabled connectors
            priority_order = [name for name in priority_order if name in self._connectors and self._connectors[name].is_enabled]
        
        if not priority_order:
            # No connectors enabled, return empty
            return []
        
        all_results = []
        
        for connector_name in priority_order:
            connector = self._connectors.get(connector_name)
            if not connector or not connector.is_enabled:
                continue
            
            # Validate connector is properly configured
            is_valid, error = connector.validate_config()
            if not is_valid:
                print(f"[{connector_name}] Skipping - not configured: {error}")
                continue
            
            try:
                results = await connector.search(query, location, limit - len(all_results))
                all_results.extend(results)
                
                if len(all_results) >= limit:
                    break
            except Exception as e:
                print(f"[{connector_name}] Failed, trying next: {e}")
                continue
        
        return all_results[:limit]


# Global connector manager instance
connector_manager = ConnectorManager()
