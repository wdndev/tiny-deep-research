import sys
sys.path.append(".")

import sys
import os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import asyncio
from tiny_deep_research.data_search import PlaywrightScraper


async def main():
    scraper = PlaywrightScraper()
    await scraper.setup()
    url = "https://zhuanlan.zhihu.com/p/1898295379990132543" 
    # 替换为你要爬取的 URL
    result = await scraper.scrape(url)
    print(f"爬取结果: {result.text}")
    await scraper.teardown()
    print("爬取完成")
    


if __name__ == '__main__':
    # main()
    asyncio.run(main())
