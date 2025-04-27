# websearch/__init__.py
from .websearch.base_search_engine import SearchResult, BaseSearchEngine
from .websearch.ddgs_search_engine import DdgsSearchEngine

# scraper/__init__.py
from .scraper.base_scraper import BaseScraper, ScrapedContent
from .scraper.playwright_scraper import PlaywrightScraper

from .search_scraper_mgr import SearchAndScrapeManager
from .search_services import SearchServiceType, SearchResponse, SearchServices