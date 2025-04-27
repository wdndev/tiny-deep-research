from enum import Enum
from typing import List, Dict, Any, Optional, TypedDict
import os
import json

from tiny_deep_research.utils import logger
from .search_scraper_mgr import SearchAndScrapeManager
from .firecrawl import Firecrawl


class SearchServiceType(Enum):
    """Search services type.
    """

    FIRECRAWL = "firecrawl"
    PLAYWRIGHT_DDGS = "playwright_ddgs"
    PLAYWRIGHT_BING = "playwright_bing"
    PLAYWRIGHT_GOOGLE = "playwright_google"

class SearchResponse(TypedDict):
    """Search response type.
    """
    data: List[Dict[str, str]]

class SearchServices:
    """Search services class.
    """
    def __init__(
        self,
        service_type: Optional[str] = None,
    ):
        """ Initialize search services.
        """
        if service_type is None:
            service_type = os.environ.get("DEFAULT_SCRAPER", "playwright_ddgs")

        self.service_type = service_type

        # Initialize search and scrape manager
        if service_type == SearchServiceType.FIRECRAWL.value:
            self.firecrawl = Firecrawl(
                api_key=os.environ.get("FIRECRAWL_API_KEY", ""),
                api_url=os.environ.get("FIRECRAWL_BASE_URL"),
            )
            self.manager = None
        elif service_type == SearchServiceType.PLAYWRIGHT_DDGS.value:
            self.manager = SearchAndScrapeManager()
            self.firecrawl = None
        else:
            self.manager = SearchAndScrapeManager()
            self.firecrawl = None
            self._initialized = False

    async def ensure_initialized(self) -> None:
        """Ensure the service is initialized.
        """
        if self.manager and not getattr(self, "_initialized", False):
            await self.manager.setup()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup the service.
        """
        if self.manager and getattr(self, "_initialized", False):
            await self.manager.teardown()
            self._initialized = False

    async def search(
        self,
        query:str, 
        limit:int = 5,
        save_content:bool = False,
        **kwargs
    ) -> Dict[str, any]:
        """Search for content using the specified service.
        """
        await self.ensure_initialized()

        try:
            if self.service_type == SearchServiceType.FIRECRAWL.value:
                firecrawl_data = await self.firecrawl.search(query, limit=limit, **kwargs)

                response = {"data": firecrawl_data}
            else:
                scraped_data = await self.manager.search_and_scrape(
                    query, num_results=limit, scrape_all=True, **kwargs
                )

                # 处理结果
                formatted_data = []
                for result in scraped_data["search_results"]:
                    item = {
                        "url": result.url,
                        "title": result.title,
                        "content": "",  # Default empty content
                    }

                    # 增加爬取的信息
                    if result.url in scraped_data["scraped_contents"]:
                        scraped = scraped_data["scraped_contents"][result.url]
                        item["content"] = scraped.text

                    formatted_data.append(item)

                response = {"data": formatted_data}
            if save_content:
                # 新建文件夹
                os.makedirs("scraped_content", exist_ok=True)

                # 保存为json文件
                for item in response.get("data", []):
                    # 标题的前50个字符作为文件名
                    title = item.get("title", "untitled")
                    safe_filename = "".join(
                        c for c in title[:50] if c.isalnum() or c in " ._-"
                    ).strip()
                    safe_filename = safe_filename.replace(" ", "_")

                    # 保存json文件
                    with open(
                        f"scraped_content/{safe_filename}.json", "w", encoding="utf-8"
                    ) as f:
                        json.dump(item, f, ensure_ascii=False, indent=2)

            return response
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return {"data": []}

        