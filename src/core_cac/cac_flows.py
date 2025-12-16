import os
import sys

# 自动找到项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from typing import List, Dict, Any
import PyPDF2
import docx2txt

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core_symbol.db_entity import ChromaDBEntity
from src.core_cac.cac_entity import EmbeddingEntity
from src.core_cac.prompt import *


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
        """构建 RAG 提示词
        参数:
            background: 相关知识背景
            docs_list: 检索到的文档列表
            query: 用户查询            
        返回:
            构建后的提示词
        """
        # 格式化文档内容
        #docs_content = "\n".join([doc.page_content for doc in docs_list])
        task_background = m2u_task_dict[task_name]
        cmd_docs = parse_cmd_dict[cmd_name]
        json_schema = json_dict[cmd_name]
        
        # 填充模板
        prompt = f"""
        <|相关知识背景|>: 这是高功率微波器件仿真软件领域，将MAGIC软件的命令式模型文件转译到UNIPIC的配置式模型文件。整个流程包括：预处理、解析、转换（三轮逻辑处理）、生成。\n
         {task_background}\n
        <|命令文档|>: {cmd_docs}\n
        <|JSON Schema|>: {json_schema}\n
        <|用户输入|>: {query}\n
        """
        return prompt


class FileLoadingFlow:
    """加载并解析文档（PDF/Word/TXT 等）"""
    def load_text(self, file_path: str) -> str:
        """加载并解析各种格式的文档文件
        参数:
            file_path: 文件路径
        返回:
            解析后的文本内容
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            # 加载 PDF 文件
            text = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text
        
        elif file_extension == '.docx':
            # 加载 Word 文档
            return docx2txt.process(file_path)
        
        elif file_extension == '.txt':
            # 加载文本文件
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}")

    def chunk_text(self, text: str, chunk_size=500, chunk_overlap=50) -> List[Document]:
        """将文本分块成适当大小的文档
        参数:
            text: 要分块的文本
            chunk_size: 块的最大大小
            chunk_overlap: 块之间的重叠大小
        返回:
            文档块列表
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # 将文本分块并创建 Document 对象
        chunks = text_splitter.create_documents([text])
        return chunks
    
    def load_and_chunk_file(self, file_path: str, chunk_size=500) -> List[Document]:
        """加载文件并直接分块
        参数:
            file_path: 文件路径
            chunk_size: 块的最大大小
        返回:
            文档块列表
        """
        text = self.load_text(file_path)
        return self.chunk_text(text, chunk_size)
    
    def add_metadata_to_chunks(self, chunks: List[Document], metadata: Dict[str, Any]) -> List[Document]:
        """为文档块添加元数据
        参数:
            chunks: 文档块列表
            metadata: 要添加的元数据字典
        返回:
            添加元数据后的文档块列表
        """
        for chunk in chunks:
            chunk.metadata.update(metadata)
        return chunks