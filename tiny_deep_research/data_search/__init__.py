# websearch/__init__.py
from .websearch.base_search import SearchResult, BaseSearchEngine
from .websearch.ddgs_search import DdgsSearchEngine
from .websearch.baidu_search import BaiduSearchEngine
from .websearch.bing_search import BingSearchEngine
from .websearch.google_search import GoogleSearchEngine

# scraper/__init__.py
from .scraper.base_scraper import BaseScraper, ScrapedContent
from .scraper.playwright_scraper import PlaywrightScraper

from .search_scraper_mgr import SearchAndScrapeManager
from .search_services import SearchServiceType, SearchResponse, SearchServices