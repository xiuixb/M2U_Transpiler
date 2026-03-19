# core/system.py
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


import asyncio
from typing import Any, Dict, List, AsyncGenerator

from rag_backend.core.config import config
from rag_backend.core.entities import (
    LCLLMEntity,
    EmbeddingEntity,
    SystemDBEntity,
    ChromaDBEntity,
    UserTableEntity,
    ChatSessionTableEntity,
    MessageTableEntity,
    MemoryTableEntity,
)
from rag_backend.core.flows import (
    MessageManageFlow,
    ChatWithHistoryFlow,
    ChromaFlow,
    RAGPromptBuildFlow,
    FileLoadingFlow,
    ChatsMemoryManageFlow,
)
from rag_backend.core.events import (
    FileLoadingEvent,
    MemoryManagementEvent,
)
from rag_backend.services import (
    UserService,
    ChatSessionService,
    RAGChatService
)


class RAGChatSystem:
    """
    主系统类（Controller 层）
    统一管理以下四大模块：
    1. Chat 管理（多轮对话）
    2. RAG 流程（知识检索 + 问答）
    3. KB 管理（知识文件嵌入）
    4. Memory 管理（长期记忆提取）
    """

    def __init__(self):
        # ========== 全局配置与核心实体 ==========
        self.config = config

        # 数据库连接（SQLite）
        self.db_entity = SystemDBEntity(self.config.sqlite_db_path)

        # 初始化数据库表实体
        self.user_table = UserTableEntity(self.db_entity)
        self.chatSession_table = ChatSessionTableEntity(self.db_entity)
        self.Message_table = MessageTableEntity(self.db_entity)
        self.memory_table = MemoryTableEntity(self.db_entity)


        # 大模型与嵌入模型
        self.llm = LCLLMEntity(
            model_name=self.config.model_name,
            api_key=self.config.model_api_key,
            system_prompt=self.config.system_prompt,
        )
        self.embedding = EmbeddingEntity(
            model_name=self.config.embedding_model,
            api_key=self.config.embedding_api_key,
        )

        # 向量数据库
        self.vector_db = ChromaDBEntity(
            vector_db_path=self.config.chroma_path,
            vector_embedding_model=self.embedding,
        )
        self.vector_flow = ChromaFlow(self.vector_db)

        # ========== 初始化辅助模块 ==========
        self.prompt_flow = RAGPromptBuildFlow()
        self.file_loader = FileLoadingFlow()
        self.user_service = UserService()

        # Memory 相关实体
        self.memory_entity = MemoryTableEntity(self.db_entity)
        self.memory_flow = ChatsMemoryManageFlow(self.memory_entity, self.llm)
        self.memory_event = MemoryManagementEvent(self.memory_flow)

        # KB 相关实体
        self.fileLd_event = FileLoadingEvent(self.file_loader, self.vector_flow)


    def init_db(self):
        """初始化数据库表"""
        print("[info] All database tables initialized successfully.")
        
    
    # =====================================================================
    # 🧠 Chat 模块：支持多轮问答（含流式）
    # =====================================================================
    def chat(self, user_name: str, chat_id: str, user_input: str) -> str:
        """
        普通问答接口（非流式）
        """
        chat_service = RAGChatService(user_name, chat_id, sys_prompt=self.config.system_prompt)
        return chat_service.chat(user_input)

    async def chat_stream(self, user_name: str, chat_id: str, user_input: str, use_rag: bool = False) -> AsyncGenerator[str, None]:
        """
        流式问答接口
        """
        chat_service = RAGChatService(user_name, chat_id, sys_prompt=self.config.system_prompt)
        async for chunk in chat_service.chat_stream(user_input, use_rag=use_rag):
            yield chunk   # type: ignore

    # =====================================================================
    # 📚 知识库（Knowledge Base）管理模块
    # =====================================================================
    def ingest_kb(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传文件 → 解析 → 切分 → 嵌入 → 存入 Chroma 向量数据库
        """
        self.fileLd_event.ingest_file(file_path, metadata)
        return {"status": "success", "message": f"知识文件 {file_path} 已入库"}

    def search_kb(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        检索知识库中最相似的文档片段
        """
        results = self.vector_flow.similarity_search(query, k)
        return results

    # =====================================================================
    # 🧩 记忆管理模块
    # =====================================================================
    def extract_memory(self, chat_history: List[Dict[str, str]]) -> str:
        """
        根据对话记录自动提取长期记忆
        """
        memory_text = self.memory_event.extract_memory(chat_history)
        return memory_text

    def store_memory(self, user_name: str, chat_id: str, memory_content: str):
        """
        保存长期记忆
        """
        self.memory_event.store_memory(user_name, chat_id, memory_content)
        return {"status": "success", "message": "记忆已保存"}

    # =====================================================================
    # 👤 用户与会话管理模块
    # =====================================================================
    def register_user(self, user_name: str, password: str):
        return self.user_service.register(user_name, password)

    def login_user(self, user_name: str, password: str) -> bool:
        return self.user_service.login(user_name, password)

    def create_chat_session(self, user_name: str, title: str, chat_type: str):
        chat_session_service = ChatSessionService(user_name)
        return chat_session_service.create_chatSession(title, chat_type)

    def list_chat_sessions(self, user_name: str):
        chat_session_service = ChatSessionService(user_name)
        return chat_session_service.list_chatSessions()
        
    def rename_chat_session(self, user_name: str, chat_id: str, new_title: str):
        chat_session_service = ChatSessionService(user_name)
        return chat_session_service.rename_chatSession(chat_id, new_title)
        
    def delete_chat_session(self, user_name: str, chat_id: str):
        chat_session_service = ChatSessionService(user_name)
        return chat_session_service.delete_chatSession(chat_id)
    
    # =====================================================================
    # 聊天记录管理模块
    # =====================================================================
    def get_chat_history(self, user_name: str, chat_id: str):
        """获取聊天记录"""
        chat_service = RAGChatService(user_name, chat_id, sys_prompt=self.config.system_prompt)
        return chat_service.get_chat_history()

    # =====================================================================
    # 🚀 辅助：异步适配器（供 FastAPI 调用）
    # =====================================================================
    async def a_chat(self, user_name: str, chat_id: str, user_input: str):
        """异步适配：普通问答"""
        return await asyncio.to_thread(self.chat, user_name, chat_id, user_input)

    async def a_ingest_kb(self, file_path: str, metadata: Dict[str, Any]):
        """异步适配：知识库上传"""
        return await asyncio.to_thread(self.ingest_kb, file_path, metadata)

    async def a_extract_memory(self, chat_history: List[Dict[str, str]]):
        """异步适配：长期记忆提取"""
        return await asyncio.to_thread(self.extract_memory, chat_history)