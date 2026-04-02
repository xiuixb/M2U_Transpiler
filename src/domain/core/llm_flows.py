import os
import sys
import json

# 自动找到项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.infrastructure.llm_entity import EmbeddingEntity
from src.infrastructure.db_entity import ChromaDBEntity
from src.domain.config.prompt import *


class EmbeddingFlow:
    """文本嵌入流程(调用阿里百炼 embedding API)"""
    def __init__(self, embedding_entity: EmbeddingEntity):
        self.embedder = embedding_entity
    
    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.embedder.embed_documents(texts)  # type: ignore
    
    def embed_query(self, text: str) -> list[float]:
        return self.embedder.embed_query(text)  # type: ignore


class ChromaFlow():
    """Chroma 向量数据库原子操作"""
    def __init__(self, chroma_db: ChromaDBEntity):
        """初始化 Chroma 向量数据库
        参数:
            persist_path: 向量数据库持久化路径
            embedding_function: 嵌入函数实例
        """
        self.db = chroma_db
    
    def add_documents(self, docs, metadatas=None, ids=None, collection_name="default"):
        """向向量数据库添加文档
        参数:
            docs: 文档列表或 Document 对象列表
            metadatas: 元数据列表（可选）
            ids: 文档ID列表(可选)
            collection_name: 集合名称，默认为"default"
        返回:
            添加的文档ID列表
        """
        self.db.insert_docs(docs=docs, ids=ids, collection_name=collection_name) # type: ignore
    
    def similarity_search(self, query, similarity_threshold=0.3, k=5, collection_name="default"):
        """根据查询文本进行相似性搜索
        参数:
            query: 查询文本
            similarity_threshold: 相似度阈值，默认为0.3
            k: 返回的最相似文档数量
            collection_name: 集合名称，默认为"default"
        返回:
            相似文档列表
        """
        return self.db.search_similar_with_score(query=query,similarity_threshold=similarity_threshold, top_k=k, collection_name=collection_name)
    
    def delete_documents(self, ids, collection_name="default"):
        """删除指定ID的文档
        参数:
            ids: 要删除的文档ID列表
            collection_name: 集合名称，默认为"default"
        """
        self.db.delete_docs(ids=ids, collection_name=collection_name)
    
    def get_documents(self, ids=None, collection_name="default"):
        """获取指定ID或所有文档
        参数:
            ids: 文档ID列表（可选，不提供则返回所有文档）
            collection_name: 集合名称，默认为"default"
        返回:
            文档列表
        """
        if ids:
            return self.db.get_doc_by_id(id_=ids, collection_name=collection_name)
        return self.db.get_all_docs(collection_name=collection_name)

    def get_docId_by_text(self, text: str, collection_name="default",col_name="content"):
        """根据文本获取文档ID
        参数:
            text: 文本内容
            collection_name: 集合名称，默认为"default"
        返回:
            文档ID
        """
        return self.db.get_docId_by_metadata(text=text, collection_name=collection_name, col_name=col_name)

    def get_doc_by_id(self, id: str, collection_name="default"):
        """根据文档ID获取文档
        参数:
            id: 文档ID
            collection_name: 集合名称，默认为"default"
        返回:
            文档对象
        """
        return self.db.get_doc_by_id(id_=id, collection_name=collection_name)


class MCLPromptBuildFlow:
    """MCL 提示词构建流程"""
    
    def build_parse_prompt(self, task_name, cmd_name, query: str) -> str:

        task_background = m2u_task_dict[task_name]
        cmd_docs = parse_cmd_dict[cmd_name]
        json_schema = json_dict[cmd_name]
        
        # 填充模板
        prompt = f"""
        <|相关知识背景|>: 这是高功率微波器件仿真软件领域，将MAGIC软件的命令式建模脚本文件转译到UNIPIC的描述式完整模型文件。整个流程包括：预处理、解析、转换（三轮逻辑处理）、生成。\n
         {task_background}\n
        <|命令文档|>: {cmd_docs}\n
        <|JSON Schema|>: {json_schema}\n
        <|用户输入|>: {query}\n
        """
        return prompt
    
    def build_mcl2mid_prompt(
                self,                
                mcl_command_type,
                mid_elements,
                mcl_cmd_text_list,
                mcl_cmd_context,
                mid_cmd_context,
                mcl2mid_json,
                mcl_payload_list                
                ):
        
        prompt = f"""
<|总体背景|>: 这是高功率微波器件仿真软件领域，整体任务是将MAGIC软件的MCL命令建模脚本文件转译到UNIPIC的描述式完整模型文件。
整个转译流程包括：参数解析、MCL到中间符号转换、中间符号到UNIPIC符号转换、UNIPIC文件生成。
<|本次任务|>: 本次任务是实现解析后的MCL命令到中间符号的转换。
请根据以下背景知识，将以下MCL命令{mcl_command_type}的参数转换为中间符号表元素{mid_elements}, mcl命令原始文本:
{mcl_cmd_text_list},
<|MCL参数知识|>: 
{mcl_cmd_context}
<|中间符号表知识|>: 
{mid_cmd_context}
<|输出输出JSON格式示例|>: 
{mcl2mid_json}
<|本次输入MCL命令参数|>: 
{json.dumps(mcl_payload_list, ensure_ascii=False, indent=4)}
<|本次输出|>:"""
        return prompt


