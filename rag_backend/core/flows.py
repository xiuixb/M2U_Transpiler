# core/complex_flows.py

from typing import Generator, List, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

import PyPDF2
import docx2txt
import os

from rag_backend.core.config import config
from rag_backend.core.entities import LCLLMEntity, MessageTableEntity, SystemDBEntity, MemoryTableEntity, EmbeddingEntity, ChromaDBEntity, UserTableEntity


class MessageManageFlow:
    """消息管理流程"""
    def __init__(self, db_entity: SystemDBEntity, user_name, chat_id, sys_prompt="You are a helpful assistant."):
        self.user_name = user_name
        self.chat_id = chat_id
        self.db_table = MessageTableEntity(db_entity)
        self.messages_dict = []
        self.max_index = 0
        self.sys_prompt = sys_prompt  # 初始化系统提示词
        self.history_pairs = config.history_pairs


    def load_history(self):
        # 获取消息历史记录
        rows = self.db_table.select(self.user_name, self.chat_id, columns=["index", "role", "content"])
        # 将元组列表转换为字典列表
        self.messages = [{"index": row[0], "role": row[1], "content": row[2]} for row in rows]
        # 修正这里的问题：从字典列表中获取最后一个元素的index值
        self.max_index = self.messages[-1]["index"] if self.messages else 0
        # 返回消息列表，只包含role和content字段
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
        # 返回消息历史记录供外部使用

    def insert_message(self, role, content):
        # 增加索引
        self.max_index += 1
        # 插入消息到数据库
        self.db_table.insert(self.user_name, self.chat_id, role, content, self.max_index)
        # 更新内存中的消息列表
        self.messages.append({"index": self.max_index, "role": role, "content": content})

    def delete_all_messages_ofChatSession(self):
        # 删除数据库中的所有消息
        self.db_table.deleteAll(self.user_name, self.chat_id)
        # 清空内存中的消息列表
        self.messages = []
        self.max_index = 0

    def delete_message(self, index):
        # 删除数据库中的消息
        self.db_table.delete_message(self.user_name, self.chat_id, index)
        # 从内存中删除消息
        self.messages = [msg for msg in self.messages if msg["index"] != index]
        # 更新最大索引
        self.max_index = max([msg["index"] for msg in self.messages]) if self.messages else 0
    
    def _build_langchain_messages(self, prompt: str, history: list):
        """构建 LangChain 消息列表（复用逻辑）"""
        lc_messages: list[SystemMessage | HumanMessage | AIMessage] = [SystemMessage(content=self.sys_prompt)]
        
        # 使用传入的历史记录或默认的历史记录
        if history is None:
            message_history = self.get_recent_history(self.history_pairs)
        else:
            message_history = history
        
        if message_history:
            for msg in message_history:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user" or role == "human":
                    lc_messages.append(HumanMessage(content=content))
                elif role == "assistant" or role == "ai":
                    lc_messages.append(AIMessage(content=content))
        
        lc_messages.append(HumanMessage(content=prompt))
        return lc_messages
    
    def get_recent_history(self, n_pairs=5):
        """获取最近 n 对问答（共 2n 条消息）"""
        rows = self.db_table.select(
            self.user_name,
            self.chat_id,
            columns=["index", "role", "content"]
        )
        messages = [{"index": row[0], "role": row[1], "content": row[2]} for row in rows]
        # 按index排序确保顺序正确
        messages.sort(key=lambda x: x["index"])
        # 取最后 n*2 条
        return messages[-n_pairs * 2:] if len(messages) > n_pairs * 2 else messages

    

class ChatWithHistoryFlow:
    """上下文对话流程, 依赖于消息管理流程"""
    def __init__(self, llm, user_name, chat_id, sys_prompt):
        self.user_name = user_name
        self.chat_id = chat_id
        self.sys_prompt = sys_prompt
        self.llm = llm

    def chat(self, messages) -> str:
        """非流式问答（保留）"""
        ai_response = self.llm.chat(messages)
        # 统一返回字符串类型
        if hasattr(ai_response, 'content'):
            return ai_response.content
        return str(ai_response)

    async def chat_stream(self, messages):
        """流式问答：返回文本片段生成器"""
        full_response = ""
        
        # 获取同步生成器（LCLLMEntity.chat_stream返回同步生成器）
        sync_generator = self.llm.chat_stream(messages)
        
        # 使用异步生成器包装同步生成器
        for chunk in sync_generator:
            if chunk:
                full_response += chunk
                yield chunk  # 实时返回片段
        
        yield {"event": "end", "full_response": full_response}


class EmbeddingFlow:
    """文本嵌入流程（调用阿里百炼 embedding API）"""
    def __init__(self, embedding_entity: EmbeddingEntity):
        self.embedder = embedding_entity
    
    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.embedder.embed_documents(texts)
    
    def embed_query(self, text: str) -> list[float]:
        return self.embedder.embed_query(text)


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
            ids: 文档ID列表（可选）
            collection_name: 集合名称，默认为"default"
        返回:
            添加的文档ID列表
        """
        self.db.insert_docs(docs=docs, ids=ids, collection_name=collection_name) # type: ignore
    
    def similarity_search(self, query, k=5, collection_name="default"):
        """根据查询文本进行相似性搜索
        参数:
            query: 查询文本
            k: 返回的最相似文档数量
            collection_name: 集合名称，默认为"default"
        返回:
            相似文档列表
        """
        return self.db.search_similar_with_score(query=query, top_k=k, collection_name=collection_name)
    
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
            return self.db.get_all_docs(collection_name=collection_name)
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



class RAGPromptBuildFlow:
    """动态构造提示词（支持 RAG + 系统指令）""" 
    def build_rag_prompt(self, retrieved_chunks, user_query, memory=""):
        """构建带上下文的 RAG 提示词
        参数:
            retrieved_chunks: 检索到的相关文档块
            user_query: 用户问题
        返回:
            构建好的提示词字符串
        """
        # 1. 构建知识上下文（只取 content，可选加入 metadata 信息）
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks):
            content = chunk["content"].strip()
            # 可选：加入来源信息（如文件名、章节）
            source = chunk["metadata"].get("source", "未知来源")
            context_parts.append(f"[参考片段 {i+1} | 来源: {source}]\n{content}")
        
        context = "\n".join(context_parts) if context_parts else "无相关知识片段"
        
        # 构造带上下文的提示词
        prompt = f"""
        <|记忆数据|>: {memory}\n
        <|用户请求|>: {user_query}\n
        <|相关知识背景|>: {context}
        """
        
        return prompt



class ChatsMemoryManageFlow:
    """根据某次对话内容自动提取/更新长期记忆"""

    def __init__(self, memory_entity: MemoryTableEntity, llm: LCLLMEntity):
        self.memory_entity = memory_entity
        self.llm = llm
        self.MemoryPrompt = """
        请根据以下对话内容，提取出与用户相关的内容保存到长期记忆，包括用户偏好、用户知识背景、用户问题场景等等。
        对话内容：{conversation}
        """
    
    def extract_memory(self, conversation: list):
        """根据对话内容提取长期记忆"""
        # 格式化提示词
        prompt = self.MemoryPrompt.format(conversation=conversation)
        
        # 调用 LLM 生成记忆内容
        memory_content = self.llm.chat(prompt)
        
        return memory_content.content

    def store_memory(self, memory_content: str, user_name: str, chat_id: str = None): # type: ignore
        # 调用 MemoryTableEntity 保存
        self.memory_entity.insert(
            user_name=user_name,
            level="long_term",
            chat_id=None,
            content=memory_content
        )



class UserManagementFlow:
    """用户管理流程"""
    def __init__(self, user_entity: UserTableEntity):
        self.user_entity = user_entity