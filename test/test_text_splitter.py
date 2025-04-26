import sys
sys.path.append(".")

import sys
import os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import unittest
from unittest.mock import patch
from tiny_deep_research.text_splitter import RecursiveCharacterTextSplitter


def main():
    text = (
        "这是一个测试文本，用于测试分割器的功能。"
        "我们将使用递归字符分割器来处理这个文本。"
        "分割器应该能够根据指定的大小和重叠来分割文本。"
        "这是第二个句子。"
        "这是第三个句子。"
    )
    chunk_size = 40
    chunk_overlap = 5

    splitter = RecursiveCharacterTextSplitter(chunk_size, chunk_overlap)
    chunks = splitter.split_text(text)

    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}: {chunk}")


if __name__ == '__main__':
    main()
