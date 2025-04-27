import os
import tiktoken

from tiny_deep_research.text_splitter import RecursiveCharacterTextSplitter

MIN_CHUNK_SIZE = 140
encoder = tiktoken.get_encoding(
    "cl100k_base"
) 

def trim_prompt(
    prompt: str, 
    context_size: int = int(os.getenv("CONTEXT_SIZE", "128000")),
) -> str:
    """
    Trim the prompt to fit within the context size.

    :param prompt: The original prompt.
    :param context_size: The maximum context size.
    :return: The trimmed prompt.
    """
    if not prompt:
        return prompt
    
    length = len(encoder.encode(prompt))
    # 无需截断
    if length <= context_size:
        return prompt

    overflow_tokens = length - context_size
    # 预估溢出字符数
    chunk_size = len(prompt) - overflow_tokens * 3
    if chunk_size < MIN_CHUNK_SIZE:
        return prompt[:MIN_CHUNK_SIZE]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,  # 默认分块大小 1000
        chunk_overlap=0
    )

    # 执行分割并取第一个有效段落
    trimmed_prompt = (
        splitter.split_text(prompt)[0] if splitter.split_text(prompt) else ""
    )

    # 处理特殊场景：分割后长度未变化（例如无合适分隔符）
    if len(trimmed_prompt) == len(prompt):
        # 递归处理前N个字符（强制缩小处理范围）
        return trim_prompt(prompt[:chunk_size], context_size)

    return trim_prompt(trimmed_prompt, context_size)
