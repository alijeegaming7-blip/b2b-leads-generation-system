"""
Scrapers package - Multi-source lead connectors.

Provides unified interface for scraping from:
- Google Maps (web scraping)
- Yelp (API)
- Yellow Pages (web scraping)
- Facebook Business (experimental scraping)
- LinkedIn Sales Navigator (OAuth + API)
- Apollo.io (B2B database)
- Hunter.io (email finder)
- Clearbit (enrichment)
- Crunchbase (startup data)
- Twitter/X (business profiles)
- ZoomInfo (enterprise, stub)
"""
from .base_connector import (
    BaseConnector,
    ConnectorResult,
    ConnectorManager,
    connector_manager,
)
from .google_maps_connector import GoogleMapsConnector
from .yelp_connector import YelpConnector
from .yellowpages_connector import YellowPagesConnector
from .facebook_connector import FacebookConnector
from .linkedin_connector import LinkedInConnector
from .apollo_connector import ApolloConnector
from .hunter_connector import HunterConnector
from .clearbit_connector import ClearbitConnector
from .crunchbase_connector import CrunchbaseConnector
from .twitter_connector import TwitterConnector
from .zoominfo_connector import ZoomInfoConnector


# Initialize global connector manager with all connectors
def init_connectors(config: dict = None):
    """
    Initialize all connectors with configuration.
    
    Args:
        config: Dict with connector configs, e.g.:
            {
                "google_maps": {"enabled": True},
                "yelp": {"api_key": "xxx", "enabled": True},
                "linkedin": {"api_key": "xxx", "enabled": False},
                "apollo": {"api_key": "xxx", "enabled": False},
                "hunter": {"api_key": "xxx", "enabled": False},
                ...
            }
    """
    config = config or {}
    
    # Register Google Maps (always available, no API key)
    gmaps_config = config.get("google_maps", {})
    gmaps = GoogleMapsConnector()
    if not gmaps_config.get("enabled", True):
        gmaps.disable()
    connector_manager.register(gmaps)
    
    # Register Yelp (requires API key)
    yelp_config = config.get("yelp", {})
    yelp = YelpConnector(api_key=yelp_config.get("api_key"))
    if not yelp_config.get("enabled", False):
        yelp.disable()
    connector_manager.register(yelp)
    
    # Register Yellow Pages (scraping, no API key)
    yp_config = config.get("yellowpages", {})
    yp = YellowPagesConnector()
    if not yp_config.get("enabled", False):
        yp.disable()
    connector_manager.register(yp)
    
    # Register Facebook (scraping, experimental)
    fb_config = config.get("facebook", {})
    fb = FacebookConnector()
    if not fb_config.get("enabled", False):
        fb.disable()
    connector_manager.register(fb)
    
    # Register LinkedIn (OAuth/API)
    linkedin_config = config.get("linkedin", {})
    linkedin = LinkedInConnector(api_key=linkedin_config.get("api_key"))
    if not linkedin_config.get("enabled", False):
        linkedin.disable()
    connector_manager.register(linkedin)
    
    # Register Apollo.io (B2B database)
    apollo_config = config.get("apollo", {})
    apollo = ApolloConnector(api_key=apollo_config.get("api_key"))
    if not apollo_config.get("enabled", False):
        apollo.disable()
    connector_manager.register(apollo)
    
    # Register Hunter.io (email finder)
    hunter_config = config.get("hunter", {})
    hunter = HunterConnector(api_key=hunter_config.get("api_key"))
    if not hunter_config.get("enabled", False):
        hunter.disable()
    connector_manager.register(hunter)
    
    # Register Clearbit (enrichment)
    clearbit_config = config.get("clearbit", {})
    clearbit = ClearbitConnector(api_key=clearbit_config.get("api_key"))
    if not clearbit_config.get("enabled", False):
        clearbit.disable()
    connector_manager.register(clearbit)
    
    # Register Crunchbase (startup data)
    crunchbase_config = config.get("crunchbase", {})
    crunchbase = CrunchbaseConnector(api_key=crunchbase_config.get("api_key"))
    if not crunchbase_config.get("enabled", False):
        crunchbase.disable()
    connector_manager.register(crunchbase)
    
    # Register Twitter/X (business profiles)
    twitter_config = config.get("twitter", {})
    twitter = TwitterConnector(api_key=twitter_config.get("api_key"))
    if not twitter_config.get("enabled", False):
        twitter.disable()
    connector_manager.register(twitter)
    
    # Register ZoomInfo (enterprise, stub)
    zoominfo_config = config.get("zoominfo", {})
    zoominfo = ZoomInfoConnector(api_key=zoominfo_config.get("api_key"))
    if not zoominfo_config.get("enabled", False):
        zoominfo.disable()
    connector_manager.register(zoominfo)


__all__ = [
    "BaseConnector",
    "ConnectorResult",
    "ConnectorManager",
    "connector_manager",
    "GoogleMapsConnector",
    "YelpConnector",
    "YellowPagesConnector",
    "FacebookConnector",
    "LinkedInConnector",
    "ApolloConnector",
    "HunterConnector",
    "ClearbitConnector",
    "CrunchbaseConnector",
    "TwitterConnector",
    "ZoomInfoConnector",
    "init_connectors",
]
