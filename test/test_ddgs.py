# import sys
# sys.path.append(".")

import sys
import os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import asyncio
from tiny_deep_research.data_search import DdgsSearchEngine


async def main():
    ddgs_search = DdgsSearchEngine()
    query = "Python 编程"
    num_results = 5

    result = await ddgs_search.search(query, num_results)
    print(f"搜索结果: {result}")


if __name__ == '__main__':
    # main()
    asyncio.run(main())
