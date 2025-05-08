import re
import numpy as np
from typing import List, Tuple, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize  # 需要安装nltk

# --- 基础模块 ---
class TextChunk:
    """增强型文本块结构"""
    __slots__ = ['content', 'source', 'window_context', 'metadata', 'vector']
    
    def __init__(
        self,
        content: str,
        source: str = "",
        window_context: str = "",
        metadata: Optional[Dict] = None,
        vector: Optional[np.ndarray] = None
    ):
        self.content = content            # 核心文本内容
        self.source = source              # 来源标识
        self.window_context = window_context  # 扩展上下文
        self.metadata = metadata or {}    # 元数据存储
        self.vector = vector              # 向量表示（可选）

    def full_text(self) -> str:
        """获取完整上下文文本"""
        return f"{self.window_context}\n{self.content}\n{self.window_context}"

# --- 核心分割器 ---
class RecursiveTextSplitter:
    """高性能递归文本分割器"""
    
    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]
        
    def _split_text(self, text: str, separator: str) -> List[str]:
        """按指定分隔符分割"""
        if separator:
            return [s for s in text.split(separator) if s]
        return [text]
    
    def _merge_splits(self, splits: List[str], separator: str) -> List[Tuple[int, int]]:
        """合并分段并记录位置"""
        merged = []
        buffer = ""
        start_idx = 0
        
        for s in splits:
            if len(buffer) + len(s) < self.chunk_size:
                buffer += s + separator
            else:
                if buffer:
                    end_idx = start_idx + len(buffer.rstrip(separator))
                    merged.append((start_idx, end_idx))
                    start_idx = end_idx - self.chunk_overlap
                    buffer = s + separator
                else:
                    merged.append((start_idx, start_idx + len(s)))
                    start_idx += len(s)
        
        if buffer:
            merged.append((start_idx, start_idx + len(buffer.rstrip(separator))))
            
        return merged

    def split_with_positions(self, text: str) -> List[Tuple[int, int]]:
        """返回(起始位置, 结束位置)列表"""
        final_chunks = []
        separators = self.separators.copy()
        separator = separators.pop(0)
        splits = self._split_text(text, separator)
        
        while len(splits) > 1 or len(separators) > 0:
            new_splits = []
            for s in splits:
                if len(s) < self.chunk_size:
                    new_splits.append(s)
                else:
                    if not separators:
                        new_splits.append(s)
                    else:
                        new_separator = separators[0]
                        new_splits.extend(self._split_text(s, new_separator))
            
            splits = new_splits
            if len(splits) == 1 and len(separators) > 0:
                separators.pop(0)
        
        return self._merge_splits(splits, separator)

# --- 进阶功能 ---
class SemanticSplitter:
    """语义感知分割器"""
    
    def __init__(self, model_name: str = 'paraphrase-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.splitter = RecursiveTextSplitter()
        
    def split_document(self, text: str, similarity_threshold: float = 0.82) -> List[TextChunk]:
        """结合语义和规则的分割"""
        # 初步规则分割
        positions = self.splitter.split_with_positions(text)
        
        # 语义调整
        sentences = sent_tokenize(text)
        sent_embeddings = self.model.encode(sentences)
        
        adjusted_chunks = []
        current_chunk = []
        current_emb = None
        
        for sent, emb in zip(sentences, sent_embeddings):
            if current_emb is not None:
                similarity = np.dot(current_emb, emb)
                if similarity < similarity_threshold:
                    adjusted_chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_emb = None
                    
            current_chunk.append(sent)
            current_emb = emb if current_emb is None else (current_emb + emb)/2
            
        if current_chunk:
            adjusted_chunks.append(" ".join(current_chunk))
            
        return self._align_chunks(text, adjusted_chunks, positions)

    def _align_chunks(self, text: str, semantic_chunks: List[str], rule_positions: List[Tuple[int, int]]) -> List[TextChunk]:
        """对齐语义分割和规则分割的结果"""
        final_chunks = []
        pointer = 0
        
        for chunk in semantic_chunks:
            start = text.find(chunk, pointer)
            if start == -1:
                continue
            end = start + len(chunk)
            
            # 寻找最近的规则分割点
            best_pos = min(rule_positions, key=lambda x: abs(x[0]-start))
            
            final_chunks.append(TextChunk(
                content=text[start:end],
                window_context=self._get_context_window(text, best_pos),
                metadata={"split_type": "semantic+rule"}
            ))
            pointer = end
            
        return final_chunks

    def _get_context_window(self, text: str, position: Tuple[int, int], window_size: int = 300) -> str:
        """获取上下文窗口"""
        start = max(0, position[0] - window_size)
        end = min(len(text), position[1] + window_size)
        return text[start:end]

# --- 处理流水线 ---
class DocumentProcessor:
    """文档处理流水线"""
    
    def __init__(self, splitter_type: str = 'semantic', **kwargs):
        self.splitter = self._init_splitter(splitter_type, **kwargs)
        
    def _init_splitter(self, splitter_type: str, **kwargs):
        if splitter_type == 'semantic':
            return SemanticSplitter(**kwargs)
        elif splitter_type == 'recursive':
            return RecursiveTextSplitter(**kwargs)
        else:
            raise ValueError(f"Unsupported splitter type: {splitter_type}")
    
    def parallel_process(
        self, 
        documents: List[Dict], 
        window_size: int = 300,
        workers: int = 4
    ) -> List[TextChunk]:
        """并行处理文档"""
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for doc in documents:
                futures.append(
                    executor.submit(
                        self.process_single,
                        doc['content'],
                        doc.get('source', ''),
                        window_size
                    )
                )
            return [f.result() for f in futures]
    
    def process_single(
        self,
        text: str,
        source: str = "",
        window_size: int = 300
    ) -> List[TextChunk]:
        """单文档处理"""
        positions = self.splitter.split_with_positions(text)
        chunks = []
        
        for start, end in positions:
            ctx_start = max(0, start - window_size)
            ctx_end = min(len(text), end + window_size)
            
            chunk = TextChunk(
                content=text[start:end],
                source=source,
                window_context=text[ctx_start:ctx_end],
                metadata={
                    "original_position": (start, end),
                    "context_window_size": ctx_end - ctx_start
                }
            )
            chunks.append(chunk)
            
        return chunks

# --- 使用示例 ---
if __name__ == "__main__":
    # 示例文档
    sample_docs = [{
        "content": """近日，Open AI的Deep Research（深度研究）功能一经推出，迅速受到诸多关注，通过将大模型+超级搜索+研究助理的三合一，金融机构一键生成报告、科研党一键生成综述成为可能。

但囿于企业场景私有化数据的敏感性以及成本问题，如何基于Deep Research做开源的本地化部署，成为不少人关心的问题。

在本篇文章里，我们将对市面上复现Deep Research的各类开源项目做一个简单的分析，并结合Deepseek等主流开源模型，推出开源项目Deep Searcher，帮助大家在企业级场景中，基于Deep Research思路，做私有化部署。这个方案也在目前常见的RAG方案上做了重大升级。""",
        "source": "nlp_intro.pdf"
    }]

    processor = RecursiveTextSplitter(
        chunk_size = 1500,
        chunk_overlap= 100
    )

    processor.sp
    
    # # 初始化处理器
    # processor = DocumentProcessor(
    #     splitter_type='recursive',
    #     chunk_size=500,
    #     chunk_overlap=30
    # )
    
    # # 处理文档
    # results = processor.parallel_process(sample_docs, workers=2)
    
    # # 输出结果
    # for idx, chunk in enumerate(results[0]):
    #     print(f"Chunk {idx+1}:")
    #     print(f"Content: {chunk.content[:50]}...")
    #     print(f"Context window: {len(chunk.window_context)} characters")
    #     print(f"Metadata: {chunk.metadata}\n")