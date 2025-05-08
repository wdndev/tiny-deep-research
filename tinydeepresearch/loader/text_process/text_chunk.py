from typing import List, Dict, Optional, Tuple, Any
import hashlib

class TextChunk:
    def __init__(
        self, 
        text: str, 
        source: str ="", 
        summary: str = "", 
        start_pos: int = 0,
        total_length: int = 0,
        metadata: Optional[Dict] = None,
        vector: Optional[Any] = None
    ):
        self.text = text                # 当前分块文本
        self.source = source            # 来源标识
        self.summary = summary          # 全文摘要（共享）
        self.start_pos = start_pos      # 在原文中的起始位置
        self.total_length = total_length # 原文总长度
        self.metadata = metadata or {}  # 元数据
        self.vector = vector            # 向量表示

    @property
    def position_ratio(self) -> float:
        """计算当前分块在原文中的占比
        """
        if self.total_length == 0:
            return 0.0
        return self.start_pos / self.total_length
    

