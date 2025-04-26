from tiny_deep_research.text_splitter.base_text_splitter import BaseTextSplitter
from typing import List, Optional

class RecursiveCharacterTextSplitter(BaseTextSplitter):
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or ["\n\n", "\n", ".", "。", "；", "，", ",", ">", "<", " ", ""]
    
    def split_text(self, text: str) -> List[str]:
        """
        将输入文本按照指定的分隔符分割成多个块，并递归地处理每个块以满足块大小限制。

        参数:
            text (str): 需要分割的原始文本。

        返回值:
            List[str]: 分割并合并后的文本块列表，每个块的大小不超过 self.chunk_size。
        """
        final_chunks: List[str] = []

        # 确定合适的分隔符，优先选择 self.separators 中第一个出现在文本中的分隔符
        separator = self.separators[-1]
        for s in self.separators:
            if s == "":
                separator = s
                break
            if s in text:
                separator = s
                break

        # 分割字符串
        splits = text.split(separator) if separator else list(text)

        # 递归处理分割后的文本
        good_splits: List[str] = []
        for s in splits:
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                # 如果当前块过大，先合并已有的小块，然后递归处理当前块
                if good_splits:
                    merged_text = self.merge_splits(good_splits, separator)
                    final_chunks.extend(merged_text)
                    good_splits = []
                other_info = self.split_text(s)
                final_chunks.extend(other_info)

        # 处理最后的剩余块
        if good_splits:
            merged_text = self.merge_splits(good_splits, separator)
            final_chunks.extend(merged_text)

        return final_chunks