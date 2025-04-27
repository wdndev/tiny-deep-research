import os
import json
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Optional, TypedDict, List

from tiny_deep_research.utils import logger
from tiny_deep_research.utils import trim_prompt
from tiny_deep_research.llm.llm_services import LLMService
from tiny_deep_research.prompt import get_system_prompt
from tiny_deep_research.data_search import SearchServices

class SearchResponse(TypedDict):
    data: List[Dict[str, str]]


class ResearchResult(TypedDict):
    learnings: List[str]
    visited_urls: List[str]


@dataclass
class SerpQuery:
    query: str
    research_goal: str

async def generate_serp_queries(
    query: str,
    llm_client: LLMService,
    num_queries: int = 3,
    learnings: Optional[List[str]] = None
) -> List[SerpQuery]:
    """ Generate SERP queries using the LLM service.
    Args:
        query (str): The original query.
        llm (LLMService): The LLM service instance.
        num_queries (int): Number of queries to generate.
        learnings (Optional[List[str]]): List of learnings to include in the prompt.
    """

    prompt_list = [
        "Given the following prompt from the user," ,
        "generate a list of SERP queries to research the topic. ",
        f"Return a JSON object with a 'queries' array field containing {num_queries} queries",
        " (or less if the original prompt is clear). ",
        "Each query object should have 'query' and 'research_goal' fields. ",
        f"Make sure each query is unique and not similar to each other: <prompt>{query}</prompt>"
    ]

    if learnings:
        prompt_list.append(f"\n\nHere are some learnings from previous research, use them to generate more specific queries: {' '.join(learnings)}")
    
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": " ".join(prompt_list)},
    ]

    llm_response = await llm_client.get_response(
        messages=messages,
        response_format={"type": "json_object"},
        stream=False,
    )

    try:
        response_json = json.loads(llm_response)
        queries = response_json.get("queries", [])
        return [SerpQuery(**q) for q in queries][:num_queries]
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {llm_response}")
        return []
    
async def process_serp_result(
    query: str,
    search_result: SearchResponse,
    llm_client: LLMService,
    num_learnings: int = 3,
    num_follow_up_questions: int = 3,
) -> Dict[str, List[str]]:
    """Process search results to extract learnings and follow-up questions.
    """

    contents = [
        trim_prompt(item.get("content", ""), 25_000)
        for item in search_result["data"]
        if item.get("content")
    ]

    contents_str = "".join(f"<content>\n{content}\n</content>" for content in contents)

    prompt = [
        f"Given the following contents from a SERP search for the query <query>{query}</query>, "
        f"generate a list of learnings from the contents. Return a JSON object with 'learnings' "
        f"and 'followUpQuestions' keys with array of strings as values. Include up to {num_learnings} learnings and "
        f"{num_follow_up_questions} follow-up questions. The learnings should be unique, "
        "concise, and information-dense, including entities, metrics, numbers, and dates.\n\n"
        f"<contents>{contents_str}</contents>"
    ]

    messages=[
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": " ".join(prompt)},
    ]

    llm_response = await llm_client.get_response(
        messages=messages,
        response_format={"type": "json_object"},
        stream=False,
    )

    try:
        response_json = json.loads(llm_response)
        return {
            "learnings": response_json.get("learnings", [])[:num_learnings],
            "followUpQuestions": response_json.get("followUpQuestions", [])[
                :num_follow_up_questions
            ],
        }
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {llm_response}")
        return {"learnings": [], "followUpQuestions": []}


async def write_final_report(
    prompt: str,
    learnings: List[str],
    visited_urls: List[str],
    llm_client: LLMService,
) -> str:
    """Write a final report based on the research results.
    """

    learnings_string = trim_prompt(
        "\n".join([f"<learning>\n{learning}\n</learning>" for learning in learnings]),
        150_000,
    )

    prompt = [
        f"Given the following prompt from the user, write a final report on the topic using "
        f"the learnings from research. Return a JSON object with a 'reportMarkdown' field "
        f"containing a detailed markdown report (aim for 3+ pages). Include ALL the learnings "
        f"from research:\n\n<prompt>{prompt}</prompt>\n\n"
        f"Here are all the learnings from research:\n\n<learnings>\n{learnings_string}\n</learnings>"
    ]

    messages=[
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": " ".join(prompt)},
    ]

    llm_response = await llm_client.get_response(
        messages=messages,
        response_format={"type": "json_object"},
        stream=False,
    )

    try:
        response_json = json.loads(llm_response)
        report = response_json.get("reportMarkdown", "")

        urls_section = "\n\n## Sources\n\n" + "\n".join(
            [f"- {url}" for url in visited_urls]
        )
        return report + urls_section
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {llm_response}")
        return "Error generating report"

async def deep_research(
    query: str,
    breadth: int,
    depth: int,
    concurrency: int,
    llm_client: LLMService,
    learnings: List[str] = None,
    visited_urls: List[str] = None,
) -> ResearchResult:
    """
    Main research function that recursively explores a topic.

    Args:
        query: 核心研究问题/主题
        breadth: 每层搜索的并行查询数量（研究广度）
        depth: 递归研究深度（0表示停止）
        concurrency: 最大并发请求数
        client: OpenAI客户端实例
        model: 使用的大模型名称
        learnings: 已积累的研究成果（用于增量研究）
        visited_urls: 已访问的URL列表（避免重复抓取）
        
    Returns:
        ResearchResult: 包含最终研究成果和访问记录的结构
    """
    learnings = learnings or []
    visited_urls = visited_urls or []

    # step 1: 生成初始搜索结果 
    serp_queries = await generate_serp_queries(
        query=query,
        llm_client=llm_client,
        num_queries=breadth,
        learnings=learnings,
    )

    # 创建信号量，控制并发数量
    semaphore = asyncio.Semaphore(concurrency)
    search_service = SearchServices(
        service_type=os.getenv("DEFAULT_SCRAPER", "playwright_ddgs")
    )

    async def process_query(serp_query: SerpQuery) -> ResearchResult:
        """处理单个SERP查询
        """
        async with semaphore:
            try:
                # Step 2: 使用搜索服务进行搜索
                result = await search_service.search(
                    serp_query.query, 
                    limit=5 
                )

                # Step 3：提取新发现的URL
                new_urls = [
                    item.get("url") 
                    for item in result["data"] 
                    if item.get("url")
                ]

                # Step 4：动态调整研究参数（广度折半，深度递减）
                new_breadth = max(1, breadth // 2)
                new_depth = depth - 1

                # Step 5：解析搜索结果（生成认知和后续问题）
                new_learnings = await process_serp_result(
                    query=serp_query.query,
                    search_result=result,
                    num_follow_up_questions=new_breadth,
                    llm_client=llm_client,
                )

                # 合并研究成果（增量式认知积累）
                all_learnings = learnings + new_learnings["learnings"]
                all_urls = visited_urls + new_urls

                # Step 6：递归执行深度研究（如果允许继续深入）
                if new_depth > 0:
                    print(
                        f"深层搜索, 广度: {new_breadth}, 深度: {new_depth}"
                    )

                    next_query = f"""
                    上层搜索目标: {serp_query.research_goal}
                    发现的新方向: {" ".join(new_learnings["followUpQuestions"])}
                    """.strip()

                    return await deep_research(
                        query=next_query,
                        breadth=new_breadth,
                        depth=new_depth,
                        concurrency=concurrency,
                        learnings=all_learnings,
                        visited_urls=all_urls,
                        llm_client=llm_client,
                    )

                # 达到最大深度时返回当前结果
                return {
                    "learnings": all_learnings, 
                    "visited_urls": all_urls
                }

            except Exception as e:
                if "Timeout" in str(e):
                    print(f"查询超时: {serp_query.query}: {e}")
                else:
                    print(f"查询错误: {serp_query.query}: {e}")
                return {"learnings": [], "visited_urls": []}

    # Step 7：并行处理本层所有查询（异步并发执行）
    results = await asyncio.gather(
        *[process_query(query) for query in serp_queries]
    )

    # Step 8：聚合最终结果（跨所有查询的去重处理）
    all_learnings = list(
        set(learning for result in results for learning in result["learnings"])
    )
    all_urls = list(set(url for result in results for url in result["visited_urls"]))

    return {
        "learnings": all_learnings, 
        "visited_urls": all_urls
    }

