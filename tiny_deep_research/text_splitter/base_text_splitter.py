from abc import ABC, abstractmethod
from typing import List, Optional


class BaseTextSplitter(ABC):
    """文本分块基类"""

    def __init__(
        self,
        chunk_size: int = 1000,  # 默认分块大小
        chunk_overlap: int = 200,  # 默认分块重叠
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Cannot have chunk_overlap >= chunk_size")

    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """将文本分块为多个 smaller 文本"""
        raise NotImplementedError("split_text is not implemented")

    def create_documents(self, texts: List[str]) -> List[str]:
        """分割文档"""
        documents = []
        for text in texts:
            for chunk in self.split_text(text):
                documents.append(chunk)
        return documents

    def split_documents(self, documents: List[str]) -> List[str]:
        """分割文档"""
        return self.create_documents(documents)

    def _join_docs(self, docs: List[str], separator: str) -> Optional[str]:
        """使用分隔符合并文档"""
        text = separator.join(docs).strip()
        return text if text else None

    def merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """
        合并分割的字符串片段为指定大小的块。

        参数:
            splits (List[str]): 需要合并的字符串片段列表。
            separator (str): 用于连接字符串片段的分隔符。

        返回:
            List[str]: 合并后的字符串块列表，每个块的大小不超过 chunk_size。

        说明:
            - 该函数根据 chunk_size 和 chunk_overlap 的限制，将输入的字符串片段合并为多个块。
            - 如果某个块的大小超过 chunk_size，会打印警告信息。
            - 使用 _join_docs 方法将片段连接成最终的字符串块。
        """
        docs: List[str] = []
        current_doc: List[str] = []
        total = 0

        for d in splits:
            _len = len(d)
            # 如果当前块加上新片段的长度超过 chunk_size，则处理当前块
            if total + _len >= self.chunk_size:
                if total > self.chunk_size:
                    print(
                        f"Created a chunk of size {total}, which is longer than the specified {self.chunk_size}"
                    )

                # 将当前块中的片段连接成一个字符串，并添加到结果列表中
                if current_doc:
                    doc = self._join_docs(current_doc, separator)
                    if doc is not None:
                        docs.append(doc)

                    # 调整当前块，确保其大小符合 chunk_overlap 的限制
                    while total > self.chunk_overlap or (
                        total + _len > self.chunk_size and total > 0
                    ):
                        total -= len(current_doc[0])
                        current_doc.pop(0)

            # 将当前片段添加到当前块中，并更新总字符数
            current_doc.append(d)
            total += _len

        # 处理最后一个块
        doc = self._join_docs(current_doc, separator)
        if doc is not None:
            docs.append(doc)

        return docs
