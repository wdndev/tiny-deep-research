# -*- coding: utf-8 -*-
import os
import asyncio
import typer
from functools import wraps
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from dotenv import load_dotenv, dotenv_values

from tiny_deep_research.deep_research import deep_research, write_final_report
from tiny_deep_research.feedback import generate_feedback
from tiny_deep_research.llm.llm_services import LLMService

load_dotenv(
    dotenv_path=".env", 
    override=True
)

app = typer.Typer()
console = Console()
session = PromptSession()

def coro(f):
    """Decorator to run async functions in a sync context.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

async def async_prompt(message: str, default: str = "") -> str:
    """ Asynchronous prompt function.
    """
    return await session.prompt_async(message, default=default)

@app.command()
@coro
async def main(
    concurrency: int = typer.Option(
        default=2, help="并发任务数."
    ),
):
    """Deep Research CLI"""
    # 标题
    console.print(
        Panel.fit(
            "[bold blue]Deep Research Assistant[/bold blue]\n"
            "[dim]An AI-powered research tool[/dim]"
        )
    )
    model_type = os.getenv("LLM_MODEL_TYPE", "")
    api_key = os.getenv("LLM_API_KEY", "")
    base_url = os.getenv("LLM_API_URL", "")
    model_name = os.getenv("LLM_MODEL_NAME", "")

    print("[SYS]: LLM_MODEL_TYPE: ", model_type)
    print("[SYS]:    LLM_API_URL: ", base_url)
    print("[SYS]: LLM_MODEL_NAME: ", model_name)

    console.print(f"🛠️ 使用 [bold green]{model_type.upper()}[/bold green] 模型服务.")

    # 模型初始化
    llm_client = LLMService(
        model_type=model_type,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name
    )

    # 交互式获取用户输入
    query = await async_prompt("\n🔍 您的研究问题是: ")
    console.print()

    # 获取搜索深度和广度
    breadth_prompt = "📊 研究广度 (推荐 2-10) [4]: "
    breadth = int((await async_prompt(breadth_prompt)) or "4")
    console.print()

    depth_prompt = "🔍 研究深度 (推荐 1-5) [2]: "
    depth = int((await async_prompt(depth_prompt)) or "2")
    console.print()

    # 生成研究计划
    console.print("\n[yellow]创建研究计划...[/yellow]")
    follow_up_questions = await generate_feedback(
        query=query,
        llm_client=llm_client, 
    )

    # 收集后续问题答案
    console.print("\n[bold yellow]子问题: [/bold yellow]")
    answers = []
    for i, question in enumerate(follow_up_questions, 1):
        console.print(f"\n[bold blue]Q{i}:[/bold blue] {question}")
        answer = await async_prompt("➤ 答案: ")
        answers.append(answer)
        console.print()

    # 组合查询参数
    combined_query = f"""
    Initial Query: {query}
    Follow-up Questions and Answers:
    {chr(10).join(f"Q: {q} A: {a}" for q, a in zip(follow_up_questions, answers))}
    """

    # 执行研究阶段（带动态进度条）
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Do research
        task = progress.add_task(
            "[yellow]正在研究您的问题...[/yellow]", total=None
        )
        research_results = await deep_research(
            query=combined_query,
            breadth=breadth,
            depth=depth,
            concurrency=concurrency,
            llm_client=llm_client,
        )
        progress.remove_task(task)

        # 展示成果
        console.print("\n[yellow]问题要点:[/yellow]")
        for learning in research_results["learnings"]:
            rprint(f"• {learning}")

        # 生成报告
        task = progress.add_task("正在生成最终报告...", total=None)
        report = await write_final_report(
            prompt=combined_query,
            learnings=research_results["learnings"],
            visited_urls=research_results["visited_urls"],
            llm_client=llm_client,
        )
        progress.remove_task(task)

        # Show results
        console.print("\n[bold green]研究完成![/bold green]")
        console.print("\n[yellow]最终报告:[/yellow]")
        console.print(Panel(report, title="Research Report"))

        # Show sources
        console.print("\n[yellow]来源:[/yellow]")
        for url in research_results["visited_urls"]:
            rprint(f"• {url}")

        # Save report
        output_path = f"outputs/report_{query[:30].replace(' ', '_')}.md"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
        console.print("\n[dim]报告已保存到 output.md 文件[/dim]")

def run():
    """Synchronous entry point for the CLI tool."""
    asyncio.run(app())


# if __name__ == "__main__":
#     # asyncio.run(app())
#     import platform
#     if platform.system().lower() == 'windows':
#         loop = asyncio.get_event_loop()
#         loop.run_until_complete(app())
#     else:
#         asyncio.run(app())

if __name__ == "__main__":
    import platform
    # Windows系统需要特殊处理
    if platform.system().lower() == 'windows':
        # 设置正确的事件循环策略
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(app())
        finally:
            loop.close()
            asyncio.set_event_loop_policy(None)  # 重置策略
    else:
        asyncio.run(app())

