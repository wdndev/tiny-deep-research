import asyncio
from openai import OpenAI, AsyncOpenAI
from typing import Generator, AsyncGenerator, Optional, Union


class LLMService:
    """LLM服务类"""

    def __init__(
        self,
        api_key: str,
        model_name: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
        model_type: str = "deepseek",
    ):
        """
        初始化LLM服务

        :param api_key: API密钥（必须）
        :param model_name: 模型名称，默认deepseek-chat
        :param base_url: API基础URL，默认deepseek
        :param model_type: 服务类型，支持openai/deepseek
        """
        if not api_key:
            raise ValueError("API key is required")

        self.model_type = model_type
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url

        self.client = AsyncOpenAI(
            api_key=api_key, base_url=None if model_type == "openai" else base_url
        )

    async def get_response(
        self,
        messages: list[dict[str, str]],
        response_format: dict = None,
        stream: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """
        获取同步LLM响应

        :param messages: OpenAI格式消息历史
        :param stream: 是否启用流式模式
        :return: 字符串或生成器
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                stream=stream,
                response_format=response_format,
            )

            if stream:
                return self._handle_stream_response(response)
            return response.choices[0].message.content

        except Exception as e:
            error_msg = f"LLM请求失败: {str(e)}"
            if stream:

                async def error_generator():
                    yield error_msg

                return error_generator()
            return error_msg

    async def _handle_stream_response(
        self, response: AsyncGenerator
    ) -> AsyncGenerator[str, None]:
        """处理流式响应"""
        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content


async def main():
    llm = LLMService(api_key="sk-xxxxxxxxxxxxxxxxxxx")
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "你好"},
    ]

    res = await llm.get_response(messages, stream=False)
    print("No Stream Response: ", res)

    # 流式调用
    print("Stream Response: ", end="", flush=True)
    res_stream = await llm.get_response(messages, stream=True)
    async for content_chunk in res_stream:
        print(content_chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
