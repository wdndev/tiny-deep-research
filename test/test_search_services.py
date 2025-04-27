import sys
sys.path.append(".")

import sys
import os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import asyncio
from tiny_deep_research.data_search import SearchServices


async def main():
    ss = SearchServices()

    result = await ss.search(
        query="Python爬虫",
        limit=5,
    )

    print(f"搜索结果: {result['data']}")
    print("搜索完成")
    await ss.cleanup()
    print("清理完成")
    


if __name__ == '__main__':
    # main()
    asyncio.run(main())
