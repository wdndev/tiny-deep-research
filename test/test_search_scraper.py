import sys
sys.path.append(".")

import sys
import os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import asyncio
from tiny_deep_research.data_search import SearchAndScrapeManager


async def main():
    ssm = SearchAndScrapeManager()

    await ssm.setup()
    
    results = await ssm.search_and_scrape(
        query="Python爬虫",
        num_results=5,
        scrape_all=True,
        max_concurrent_scrapes=2,
    )
    print(f"搜索结果: {results['search_results']}")
    print(f"爬取结果: {results['scraped_contents']}")

    await ssm.teardown()
    print("搜索和爬取完成")
    


if __name__ == '__main__':
    # main()
    asyncio.run(main())
