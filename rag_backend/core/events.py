


from rag_backend.core.flows import *

class RAGChatEvent:
    """检索增强生成事件：结合知识库 + 对话历史"""
    def __init__(self, 
                 message_flow: MessageManageFlow,
                 Chat_flow: ChatWithHistoryFlow, 
                 vectorDB_flow: ChromaFlow, 
                 prompt_flow: RAGPromptBuildFlow ):
        self.message_flow = message_flow
        self.Chat_flow = Chat_flow
        self.vectorDB_flow = vectorDB_flow
        self.prompt_flow = prompt_flow

    def get_chat_history(self):
        """获取聊天记录"""
        return self.message_flow.load_history()
        
    def rag_chat(self, user_query: str, chat_history: list) -> str:
        """同步RAG问答：结合知识库和对话历史"""
        # 1. 从向量数据库检索相关文档
        docs_list = self.vectorDB_flow.similarity_search(user_query, k=5)
        
        # 2. 构建带上下文的提示词
        prompt = self.prompt_flow.build_rag_prompt(docs_list, user_query, "")
        
        # 3. 构建LangChain消息格式（使用传入的对话历史）
        lc_messages = self.message_flow._build_langchain_messages(prompt, chat_history)
        
        # 4. 调用LLM获取回答
        ai_response = self.Chat_flow.chat(lc_messages)
        
        # 5. 保存对话记录到消息管理流程
        self.message_flow.insert_message("human", user_query)
        self.message_flow.insert_message("ai", ai_response)
        
        return ai_response

    async def rag_chat_stream(self, user_query: str, chat_history: list):
        """流式问答：返回文本片段生成器"""
        # 1. 从向量数据库检索相关文档
        docs_list = self.vectorDB_flow.similarity_search(user_query, k=5)
        
        # 2. 构建带上下文的提示词
        prompt = self.prompt_flow.build_rag_prompt(docs_list, user_query, "")
        
        # 3. 构建LangChain消息格式（使用传入的对话历史）
        lc_messages = self.message_flow._build_langchain_messages(prompt, chat_history)
        
        # 4. 流式调用LLM获取回答
        full_response = ""
        async for chunk in self.Chat_flow.llm.chat_stream(lc_messages):
            full_response += chunk
            yield chunk  # 实时返回片段
        
        # 5. 保存完整的对话记录
        self.message_flow.insert_message("human", user_query)
        self.message_flow.insert_message("ai", full_response)

        yield {"event": "end", "full_response": full_response}


class MemoryManagementEvent:
    def __init__(self, memory_flow: ChatsMemoryManageFlow):
        self.LMemFlow = memory_flow

    """根据对话内容自动提取/更新长期记忆"""
    def extract_memory(self, conversation: list) -> str:
        # 调用 LLM 总结关键信息
        memory_content = self.LMemFlow.extract_memory(conversation)
        return memory_content  # type: ignore

    def store_memory(self, user_name: str, chat_id: str , memory_content: str): 
        # 调用 MemoryTableEntity 保存
        self.LMemFlow.store_memory(memory_content, user_name, chat_id)


class FileLoadingEvent:
    """上传文件 → 解析 → 切分 → 嵌入 → 存入 Chroma"""
    def __init__(self, file_loading_flow: FileLoadingFlow, vectorDB_flow: ChromaFlow):
        self.file_loading_flow = file_loading_flow
        self.vectorDB_flow = vectorDB_flow

    def ingest_file(self, file_path: str, metadata: dict):
        """上传文件 → 解析 → 切分 → 嵌入 → 存入 Chroma"""
        # 解析文件
        docs = self.file_loading_flow.load_text(file_path)
        # 切分文档
        split_docs = self.file_loading_flow.chunk_text(docs)
        # 向 Chroma 数据库添加文档
        self.vectorDB_flow.add_documents(split_docs, metadatas=[metadata]*len(split_docs))