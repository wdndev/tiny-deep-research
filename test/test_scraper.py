
import sys
import os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import json
import asyncio
import readabilipy.simple_json
from tiny_deep_research.data_search import BingSearchEngine, BaiduSearchEngine, GoogleSearchEngine, DdgsSearchEngine
from tiny_deep_research.data_search import SearchAndScrapeManager, PlaywrightScraper, BaseSearchEngine, BaseScraper


async def main():
    search_engine = BaiduSearchEngine()
    scraper = PlaywrightScraper()
    # query = "模型上下文协议（MCP）"
    query = "Python 教程"
    num_results = 5

    search_results = await search_engine.search(query, num_results)
    print(f"搜索结果: {search_results}")

    scraped_contents = []
    for result in search_results:
        url = result.url
        scraped_result = await scraper.scrape(url)
        # scraped_contents[url] = scraped_result

        # ret = readabilipy.simple_json.simple_json_from_html_string(
        #     scraped_result.html, use_readability=True
        # )

        scraped_contents.append({
            "url": result.url,
            "title": result.title,
            "content": scraped_result.text,
            # "html": scraped_result.html,
        })

    os.makedirs(f"logs/{query}", exist_ok=True)
    for item in scraped_contents:
        title = item.get("title", "untitled")
        safe_filename = "".join(
            c for c in title[:50] if c.isalnum() or c in " ._-"
        ).strip()
        safe_filename = safe_filename.replace(" ", "_")
        # 保存json文件
        with open(
            f"logs/{query}/{safe_filename}.json", "w", encoding="utf-8"
        ) as f:
            json.dump(item, f, ensure_ascii=False, indent=2)

    print(f"爬取结果结束")







if __name__ == '__main__':
    # main()
    asyncio.run(main())