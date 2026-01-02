"""
service 层：负责将实体/流程/事件组合成面向上层调用的服务，
- 统一读取 config
- 创建并持有底层实体
- 进行参数校验与错误转换
- 提供稳定、清晰的服务接口

注意：当前仓库处于重构中，flows/events 中的部分接口命名存在不一致。
本文件尽量只在服务层内消化适配，避免扩大改动范围。
"""

from typing import List, Dict, Any
import sqlite3

from rag_backend.core.config import config
from rag_backend.core.entities import (
    SystemDBEntity,
    UserTableEntity,
    ChatSessionTableEntity,
)
from rag_backend.core.flows import (
    MessageManageFlow,
    ChatWithHistoryFlow,
    ChromaFlow,
    RAGPromptBuildFlow,
)

from rag_backend.core.entities import LCLLMEntity, EmbeddingEntity, ChromaDBEntity


class UserService:
    """用户管理服务"""

    def __init__(self):
        self.db_entity = SystemDBEntity(config.sqlite_db_path)
        self.user_table = UserTableEntity(self.db_entity)

    def register(self, user_name: str, password: str, info: Any = "{}") -> str:
        if not user_name or not password:
            raise ValueError("用户名和密码不能为空")
        try:
            return self.user_table.addUser(user_name, password, info)
        except sqlite3.IntegrityError as e:
            raise ValueError(f"用户注册失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"注册过程发生错误：{str(e)}")

    def delete(self, user_name: str) -> int:
        if not user_name:
            raise ValueError("用户名不能为空")
        try:
            return self.user_table.deleteUser(user_name)
        except sqlite3.Error as e:
            raise RuntimeError(f"删除用户失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"删除过程发生错误：{str(e)}")

    def update_info(self, user_name: str, info: Any) -> int:
        if not user_name:
            raise ValueError("用户名不能为空")
        try:
            return self.user_table.updateUserInfo(user_name, info)
        except sqlite3.Error as e:
            raise RuntimeError(f"更新用户信息失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"更新过程发生错误：{str(e)}")

    def get_info(self, user_name: str) -> Any:
        if not user_name:
            raise ValueError("用户名不能为空")
        try:
            return self.user_table.getUserInfo(user_name)
        except sqlite3.Error as e:
            raise RuntimeError(f"获取用户信息失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"获取过程发生错误：{str(e)}")

    def login(self, user_name: str, password: str) -> bool:
        if not user_name or not password:
            raise ValueError("用户名与密码不能为空")
        try:
            return self.user_table.checkUser(user_name, password)
        except sqlite3.Error as e:
            raise RuntimeError(f"登录验证失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"登录过程发生错误：{str(e)}")


class ChatSessionService:
    """会话管理服务（按用户）"""

    def __init__(self, user_name: str):
        if not user_name:
            raise ValueError("user_name 不能为空")
        self.db_entity = SystemDBEntity(config.sqlite_db_path)
        self.chatSession_table = ChatSessionTableEntity(self.db_entity)
        self.user_name = user_name

    def list_chatSessions(self) -> List[Dict[str, Any]]:
        """列出用户的全部会话，返回字典列表"""
        try:
            rows = self.chatSession_table.select(
                user_name=self.user_name,
                columns=["user_name", "chat_id", "title", "type"]
            )
            return [
                {"user_name": r[0], "chat_id": r[1], "title": r[2], "type": r[3]}
                for r in rows
            ]
        except sqlite3.Error as e:
            raise RuntimeError(f"查询会话列表失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"获取会话列表过程发生错误：{str(e)}")

    def create_chatSession(self, title: str, chat_type: str) -> str:
        if not title:
            raise ValueError("title 不能为空")
        if not chat_type:
            raise ValueError("chat_type 不能为空")
        try:
            # insert 会内部生成 chat_id
            return self.chatSession_table.insert(self.user_name, None, title, chat_type)
        except sqlite3.IntegrityError as e:
            raise ValueError(f"创建会话失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"创建会话过程发生错误：{str(e)}")

    def delete_chatSession(self, chat_id: str) -> int:
        if not chat_id:
            raise ValueError("chat_id 不能为空")
        try:
            return self.chatSession_table.delete(
                where="user_name = ? AND chat_id = ?",
                params=(self.user_name, chat_id),
            )
        except sqlite3.Error as e:
            raise RuntimeError(f"删除会话失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"删除会话过程发生错误：{str(e)}")

    def rename_chatSession(self, chat_id: str, new_title: str) -> int:
        if not chat_id:
            raise ValueError("chat_id 不能为空")
        if not new_title:
            raise ValueError("new_title 不能为空")
        try:
            return self.chatSession_table.update(
                data={"title": new_title},
                where="user_name = ? AND chat_id = ?",
                params=(self.user_name, chat_id),
            )
        except sqlite3.Error as e:
            raise RuntimeError(f"重命名会话失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"重命名会话过程发生错误：{str(e)}")


class RAGChatService:
    """RAG 多轮对话服务（骨架）
    说明：先实现最小可用形态（系统提示 + 历史对话 + 同步问答），并在服务层完成消息落库；
    后续可接入检索（ChromaFlow）与提示拼装（RAGPromptBuildFlow），以及流式输出。
    """

    def __init__(self, user_name: str, chat_id: str, sys_prompt: str | None = None):
        if not user_name or not chat_id:
            raise ValueError("user_name 与 chat_id 不能为空")

        try:
            self.db_entity = SystemDBEntity(config.sqlite_db_path)
            self.user_name = user_name
            self.chat_id = chat_id
            self.sys_prompt = sys_prompt or config.system_prompt

            # LLM 与消息流
            self.llm = LCLLMEntity(config.model_name, config.model_api_key, self.sys_prompt)
            self.msg_flow = MessageManageFlow(self.db_entity, user_name, chat_id)
            # 补齐 MessageManageFlow 需要的系统提示
            setattr(self.msg_flow, "sys_prompt", self.sys_prompt)

            # RAG 与对话流（按需使用）
            self._embedding = EmbeddingEntity(config.embedding_model, config.embedding_api_key)
            self._chroma = ChromaDBEntity(config.chroma_path, self._embedding)
            self.vector_flow = ChromaFlow(self._chroma)
            self.prompt_flow = RAGPromptBuildFlow()
            self.chat_flow = ChatWithHistoryFlow(self.llm, user_name, chat_id, self.sys_prompt)
        except Exception as e:
            raise RuntimeError(f"初始化RAG对话服务失败：{str(e)}")

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """获取聊天记录"""
        return self.msg_flow.load_history()


    def chat(self, user_input: str) -> str:
        """非流式：返回回答文本并落库"""
        if not user_input:
            raise ValueError("user_input 不能为空")

        try:
            # 1) 加载历史
            self.msg_flow.load_history()

            # 2) 简版消息构建（如需 RAG：先检索再 build prompt）
            docs = self.vector_flow.similarity_search(user_input, k=5)
            prompt = self.prompt_flow.build_rag_prompt(docs, user_input)

            history_messages = self.msg_flow.get_recent_history(config.history_pairs)
            print("history_messages:\n",history_messages)

            messages = self.msg_flow._build_langchain_messages(prompt, history_messages)

            # 3) 模型调用
            ai_message = self.chat_flow.chat(messages)
            answer_text = getattr(ai_message, "content", str(ai_message))

            # 4) 落库
            self.msg_flow.insert_message("human", user_input)
            self.msg_flow.insert_message("ai", answer_text)

            return answer_text
        except sqlite3.Error as e:
            raise RuntimeError(f"数据库操作失败：{str(e)}")
        except Exception as e:
            raise RuntimeError(f"对话过程发生错误：{str(e)}")
    
    async def chat_stream(self, user_input: str, use_rag: bool = True):
        """流式对话（支持 RAG）"""
        try:
            # 1) 加载历史
            self.msg_flow.load_history()
            
            # 2) 构造消息（可选 RAG）
            if use_rag:
                docs = self.vector_flow.similarity_search(user_input, k=5)
                prompt = self.prompt_flow.build_rag_prompt(docs, user_input, "")
                history_messages = self.msg_flow.get_recent_history(config.history_pairs)
                messages = self.msg_flow._build_langchain_messages(prompt, history_messages)
            else:
                history_messages = self.msg_flow.get_recent_history(config.history_pairs)
                messages = self.msg_flow._build_langchain_messages(user_input, history_messages)
            
            # 3) 流式调用并向上游转发
            full_response = ""
            async for chunk in self.chat_flow.chat_stream(messages):
                if isinstance(chunk, dict) and chunk.get("event") == "end":
                    full_resp = chunk.get("full_response", "")
                    # 4) 在流结束时落库
                    self.msg_flow.insert_message("human", user_input)
                    self.msg_flow.insert_message("ai", full_resp)
                    yield chunk
                else:
                    # 逐片段透传
                    full_response += chunk if isinstance(chunk, str) else str(chunk)
                    yield chunk
                    
        except sqlite3.Error as e:
            import traceback
            error_trace = traceback.format_exc()
            raise RuntimeError(f"数据库操作失败：{str(e)}\n详细错误路径:\n{error_trace}")
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            raise RuntimeError(f"流式对话过程发生错误：{str(e)}\n详细错误路径:\n{error_trace}")