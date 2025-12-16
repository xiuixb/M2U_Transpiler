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

import re
import json
import sqlite3
import logging
import threading
from typing import Optional, List, Dict, Any
from neo4j import GraphDatabase, Query
import uuid
from datetime import datetime

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document

from src.core_cac.cac_entity import EmbeddingEntity

class SystemDBEntity:
    """系统数据库实体（管理SQLite）"""
    _lock = threading.Lock()
    def __init__(self, db_path):
        self.conn = sqlite3.connect(database=db_path, check_same_thread=False)

    def execute(self, query, params=()):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(query, params)
            self.conn.commit()
            return cur.fetchall()

class DBTableEntity:
    """数据库表实体"""
    def __init__(self, db_entity: SystemDBEntity, table_name: str):
        self.db_conn = db_entity.conn
        self.table_name = table_name
        self._lock = db_entity._lock  # 使用SystemDBEntity的锁

    def insert(self, data):
        """插入数据到表中
        参数:
            data: 字典，键为列名，值为要插入的数据
        返回:
            插入的行数
        """
        columns = ', '.join([f'"{col}"' if col.lower() == 'index' else col for col in data.keys()])
        placeholders = ', '.join(['?' for _ in data.values()])
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        with self._lock:
            cur = self.db_conn.cursor()
            try:
                cur.execute(query, tuple(data.values()))
                self.db_conn.commit()
                return cur.rowcount
            except sqlite3.IntegrityError as e:
                self.db_conn.rollback()
                raise ValueError(f"插入数据失败：{str(e)}")

    def select(self, columns=None, where=None, params=()):
        """从表中查询数据
        参数:
            columns: 列表，要查询的列名，默认为所有列
            where: 字符串，WHERE子句条件
            params: 元组，WHERE子句的参数值
        返回:
            查询结果列表
        """
        if columns is None:
            columns_str = '*'
        else:
            # 对columns中的每个列名进行处理，如果是index字段则添加反引号
            processed_columns = []
            for col in columns:
                if col.lower() == 'index':
                    processed_columns.append('`index`')
                elif col.lower() == '`index`':
                    processed_columns.append(col)  # 如果已经有反引号则保持不变
                else:
                    processed_columns.append(col)
            columns_str = ', '.join(processed_columns)
        
        query = f"SELECT {columns_str} FROM {self.table_name}"
        
        if where:
            query += f" WHERE {where}"
        
        with self._lock:
            cur = self.db_conn.cursor()
            cur.execute(query, params)
            return cur.fetchall()

    def update(self, data, where, params=()):
        """更新表中的数据
        参数:
            data: 字典，键为列名，值为要更新的数据
            where: 字符串，WHERE子句条件
            params: 元组，WHERE子句的参数值
        返回:
            更新的行数
        """
        set_clause = ', '.join([f'"{col}" = ?' if col.lower() == 'index' else f"{col} = ?" for col in data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {where}"
        
        # 合并数据值和WHERE参数
        all_params = tuple(data.values()) + params
        
        with self._lock:
            cur = self.db_conn.cursor()
            try:
                cur.execute(query, all_params)
                self.db_conn.commit()
                return cur.rowcount
            except sqlite3.IntegrityError as e:
                self.db_conn.rollback()
                raise ValueError(f"更新数据失败：{str(e)}")

    def delete(self, where, params=()):
        """删除表中的数据
        参数:
            where: 字符串，WHERE子句条件
            params: 元组，WHERE子句的参数值
        返回:
            删除的行数
        """
        query = f"DELETE FROM {self.table_name} WHERE {where}"
        
        with self._lock:
            cur = self.db_conn.cursor()
            try:
                cur.execute(query, params)
                self.db_conn.commit()
                return cur.rowcount
            except sqlite3.IntegrityError as e:
                self.db_conn.rollback()
                raise ValueError(f"删除数据失败：{str(e)}")
    
    def countByValue(self, **kwargs):
        """统计表中多个列具有特定值的记录数量
        参数:
            **kwargs: 列名和值的键值对
        返回:
            符合条件的记录数量（整数）
        """
        if not kwargs:
            return 0
        
        conditions = [f'"{col}" = ?' if col.lower() == 'index' else f"{col} = ?" for col in kwargs.keys()]
        where_clause = " AND ".join(conditions)
        query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}"
        
        with self._lock:
            cur = self.db_conn.cursor()
            cur.execute(query, tuple(kwargs.values()))
            result = cur.fetchone()
            return result[0] if result else 0

class UserTableEntity(DBTableEntity):
    """用户表实体"""
    def __init__(self, db_entity: SystemDBEntity):
        super().__init__(db_entity, "users")
        self.create_table()
    
    def create_table(self):
        """创建用户表"""
        query = """
        CREATE TABLE IF NOT EXISTS users (
            user_name TEXT PRIMARY KEY,
            password TEXT,
            info JSON
        )
        """
        with self._lock:
            cur = self.db_conn.cursor()
            cur.execute(query)
            self.db_conn.commit()

        # 插入默认用户
        if not self.checkuser_nameExists("admin"):
            admin_user = {
                "user_name": "admin",
                "password": "123456",
                "info": "{}"
            }
            self.insert(admin_user)

    def checkuser_nameExists(self, user_name):
        """检查用户名是否已存在"""
        query = "SELECT 1 FROM users WHERE user_name = ?"
        with self._lock:
            cur = self.db_conn.cursor()
            cur.execute(query, (user_name,))
            return cur.fetchone() is not None

    def checkUser(self, user_name, password):
        """检查用户是否存在"""
        query = "SELECT * FROM users WHERE user_name = ? AND password = ?"
        with self._lock:
            cur = self.db_conn.cursor()
            cur.execute(query, (user_name, password))
            result = cur.fetchone()
            return result is not None

    def addUser(self, user_name, password, info="{}"):
        """注册用户"""
        if self.checkuser_nameExists(user_name):
            raise ValueError(f"用户名 {user_name} 已存在")

        data = {
            "user_name": user_name,
            "password": password,
            "info": info
        }

        self.insert(data)
        return user_name

    def deleteUser(self, user_name):
        """删除用户"""
        return self.delete(f"user_name = ?", (user_name,))

    def updateUserInfo(self, user_name, info):
        """更新用户信息"""
        
        if isinstance(info, dict):
            info = json.dumps(info)
        return self.update({"info": info}, f"user_name = ?", (user_name,))

    def getUserInfo(self, user_name):
        """获取用户信息"""
        query = "SELECT info FROM users WHERE user_name = ?"
        with self._lock:
            cur = self.db_conn.cursor()
            cur.execute(query, (user_name,))
            result = cur.fetchone()
            return result[0] if result else "{}"

class ChatSessionTableEntity(DBTableEntity):
    """
    会话表实体
    包含用户ID、会话ID、标题、类型字段
    """
    
    def __init__(self, db_entity: SystemDBEntity):
        super().__init__(db_entity, "chatSessions")
        self.create_table()

    def create_table(self):
        """创建会话表"""
        query = """
        CREATE TABLE IF NOT EXISTS chatSessions (
            user_name TEXT,
            chat_id TEXT PRIMARY KEY,
            title TEXT,
            type TEXT
        )
        """
        with self._lock:
            cur = self.db_conn.cursor()
            cur.execute(query)
            self.db_conn.commit()

    def insert(self, user_name, chat_id, title, chat_type):
        """插入会话数据"""
        data = {
            "user_name": user_name,
            "chat_id": str(uuid.uuid4()),
            "title": title,
            "type": chat_type
        }
        super().insert(data)
        return data["chat_id"]
    
    def select(self, user_name, columns=None, where=None, params=()):
        """查询用户会话"""
        if where:
            where = f"user_name = ? AND {where}"
        else:
            where = "user_name = ?"
        params = (user_name,) + params
        return super().select(columns, where, params)
    
    def delete_session(self, user_name, chat_id):
        """删除用户会话"""
        return super().delete(f"user_name = ? AND chat_id = ?", (user_name, chat_id))
    
    def update_session(self, user_name, chat_id, title=None, chat_type=None):
        """更新会话数据"""
        data = {}
        if title is not None:
            data["title"] = title
        if chat_type is not None:
            data["type"] = chat_type
        if not data:
            return 0
        return super().update(data, f"user_name = ? AND chat_id = ?", (user_name, chat_id))
    
    def countUserChatSessions(self, user_name):
        """统计用户会话数量"""
        return self.countByValue(user_name=user_name)
    
    def countByType(self, chat_type):
        """统计会话类型数量"""
        return self.countByValue(type=chat_type)

class MessageTableEntity(DBTableEntity):
    """
    消息表实体
    包含会话ID、会话相对次序、角色、内容、创建时间字段
    主键为（chat_id, index）
    """
    def __init__(self, db_entity: SystemDBEntity):
        super().__init__(db_entity, "messages")
        self.create_table()

    def create_table(self):
        """创建消息表"""
        query = """
        CREATE TABLE IF NOT EXISTS messages (
            user_name TEXT,
            chat_id TEXT,
            `index` INTEGER,
            role TEXT,
            content TEXT, 
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (chat_id, `index`)
        )
        """
        with self._lock:
            cur = self.db_conn.cursor()
            cur.execute(query)
            self.db_conn.commit()

    def insert(self, user_name, chat_id, role, content, index):
        """插入消息数据"""
        data = {
            "user_name": user_name,
            "chat_id": chat_id,
            "index": index,
            "role": role,
            "content": content,
            "create_time": datetime.now()
        }
        return super().insert(data)

    def select(self, user_name, chat_id, columns=None, where=None, params=()):
        """查询会话消息"""
        if where:
            where = f"user_name = ? AND chat_id = ? AND {where}"
        else:
            where = "user_name = ? AND chat_id = ?"
        params = (user_name, chat_id) + params
        return super().select(columns, where, params)
    
    def deleteAll(self, user_name, chat_id):
        """清空会话消息"""
        return super().delete(f"user_name = ? AND chat_id = ?", (user_name, chat_id))
    
    def delete_message(self, user_name, chat_id, index):
        """删除会话消息"""
        return super().delete(f"user_name = ? AND chat_id = ? AND `index` = ?", (user_name, chat_id, index))
    
    def countByChatId(self, user_name, chat_id):
        """统计会话消息数量"""
        return self.countByValue(user_name=user_name, chat_id=chat_id)

class MemoryTableEntity(DBTableEntity):
    """
    记忆表实体
    包含记忆ID、用户ID、记忆级别、会话ID、记忆内容、创建时间字段
    """
    def __init__(self, db_entity: SystemDBEntity):
        super().__init__(db_entity, "memories")
        self.create_table()

    def create_table(self):
        """创建记忆表"""
        query = """
        CREATE TABLE IF NOT EXISTS memories (
            memory_id TEXT PRIMARY KEY,
            user_name TEXT,
            level TEXT,
            chat_id TEXT,
            content TEXT, 
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        with self._lock:
            cur = self.db_conn.cursor()
            cur.execute(query)
            self.db_conn.commit()

    def insert(self, user_name, level, chat_id, content):
        """插入记忆数据"""
        memory_id = str(uuid.uuid4())
        data = {
            "memory_id": memory_id,
            "user_name": user_name,
            "level": level,
            "chat_id": chat_id,
            "content": content,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return super().insert(data)
    
    def select(self, memory_id, user_name, level, chat_id, columns=None, where=None, params=()):
        """查询记忆数据"""
        if where:
            where = f"memory_id = ? AND user_name = ? AND level = ? AND chat_id = ? AND {where}"
        else:
            where = "memory_id = ? AND user_name = ? AND level = ? AND chat_id = ?"
        params = (memory_id, user_name, level, chat_id) + params
        return super().select(columns, where, params)
    
    def delete_memory(self, user_name, level, chat_id):
        """删除记忆数据"""
        return super().delete(f"user_name = ? AND level = ? AND chat_id = ?", (user_name, level, chat_id))
    
    def update_memory(self, memory_id, user_name, level, chat_id, data):
        """更新记忆数据"""
        return super().update(data, f"memory_id = ? AND user_name = ? AND level = ? AND chat_id = ?", (memory_id, user_name, level, chat_id))

    def countByLevel(self, user_name, level, chat_id):
        """统计记忆级别数量"""
        return self.countByValue(user_name=user_name, level=level, chat_id=chat_id)

class VectorDBEntity:
    """向量数据库实体"""
    def __init__(self, vector_db_path: str, vector_embedding_model:EmbeddingEntity):
        """
        参数:
            vector_db_path: 向量数据库存储路径
            vector_embedding_model: 一个EmbeddingEntity对象，其属性 .model 为可调用embedding函数
        """
        self.db_path = vector_db_path
        self.embedding_fn = vector_embedding_model.model


class ChromaDBEntity(VectorDBEntity):
    """ChromaDB 实体"""

    def __init__(self, vector_db_path: str, vector_embedding_model:EmbeddingEntity):
        """
        参数:
            vector_db_path: 向量数据库存储路径
            vector_embedding_model: 一个EmbeddingEntity对象，其属性 .model 为可调用embedding函数
        """
        super().__init__(vector_db_path, vector_embedding_model)
        self.db_conn = Chroma(persist_directory=self.db_path, embedding_function=self.embedding_fn)
        self.init_table()

    def init_table(self):
        """可用于在首次创建数据库时初始化默认集合"""
        # 创建默认集合
        default_collection = self._get_or_create_collection("default")
        
        # 创建"text_segments"集合（文本段）
        text_segment_collection = self._get_or_create_collection("text_segments")
        
        # 创建"discussion_objects"集合（讨论对象）
        discussion_object_collection = self._get_or_create_collection("discussion_objects")
        
        print(f"[INFO] ChromaDB initialized at {self.db_path}")
        print(f"[INFO] Created collections: default, text_segments, discussion_objects")

    # ---------------------- CRUD 操作 ---------------------- #
    
    def insert_docs(self, docs: List[Document], ids: List[str], collection_name: str = "default"):
        """插入文档到向量数据库"""
        db = self._get_or_create_collection(collection_name)
        db.add_documents(docs, ids=ids)
        db.persist()
        print(f"[INFO] Inserted {len(docs)} docs into collection '{collection_name}'")

    def search_similar(
        self, query: str, top_k: int = 5, collection_name: str = "default"
    ) -> List[Document]:
        """相似度搜索"""
        db = self._get_or_create_collection(collection_name)
        results = db.similarity_search(query, k=top_k)
        return results

    def search_similar_with_score(
        self, query: str, similarity_threshold, top_k: int = 5, collection_name: str = "default"
    ) -> List[Dict[str, Any]]:
        """带相似度得分的搜索"""
        db = self._get_or_create_collection(collection_name)
        results = db.similarity_search_with_relevance_scores(query, k=top_k)

        threshold = similarity_threshold

        filtered = []
        for doc, score in results:
            if score is None or score < threshold:
                continue
            filtered.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })

        # 按得分降序排列，取前 top_k 个
        filtered.sort(key=lambda x: x["score"], reverse=True)
        return filtered[:top_k]

    def delete_docs(self, ids: List[str], collection_name: str = "default"):
        """删除指定id的文档"""
        db = self._get_or_create_collection(collection_name)
        db.delete(ids=ids)
        db.persist()
        print(f"[INFO] Deleted {len(ids)} docs from '{collection_name}'")

    def update_doc(
        self, id_: str, new_content: str, metadata: Optional[Dict[str, Any]] = None,
        collection_name: str = "default"
    ):
        """更新指定文档（删除再插入）"""
        self.delete_docs([id_], collection_name)
        new_doc = Document(page_content=new_content, metadata=metadata or {})
        self.insert_docs([new_doc], [id_], collection_name)
        print(f"[INFO] Updated doc {id_} in '{collection_name}'")

    def _get_or_create_collection(self, collection_name: str = "default") -> Chroma:
        """获取或创建collection"""
        return Chroma(
            persist_directory=self.db_path,
            collection_name=collection_name,
            embedding_function=self.embedding_fn
        )
    
    def get_doc_by_id(self, id_: str, collection_name: str = "default") -> Optional[Document]:
        """根据ID获取文档内容"""
        db = self._get_or_create_collection(collection_name)
        results = db.get(ids=[id_])
        return results["documents"][0] if results["documents"] else None
    
    def get_docId_by_metadata(self, text: str, collection_name: str = "default", col_name: str = "content") -> Optional[str]:
        """根据元数据文本获取文档ID"""
        db = self._get_or_create_collection(collection_name)
        results = db.get(where={col_name: {"$eq": text}})
        return results["ids"][0] if results["ids"] else None

    def get_all_docs(self, collection_name: str = "default") -> List[dict]:
        """加载所有文档, 返回 [{'id':..., 'content':..., 'metadata':...}]"""
        db = self._get_or_create_collection(collection_name)
        results = db.get()
        ids = results.get("ids", [])
        docs = results.get("documents", [])
        metas = results.get("metadatas", [])

        out = []
        for i in range(len(ids)):
            out.append({
                "id": ids[i],
                "content": docs[i],
                "metadata": metas[i] if i < len(metas) else {}
            })
        return out


# 配置日志系统
# 确保日志目录存在
LOG_PATH = os.path.join(project_root, "log", "kg_db.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

neo4j_logger = logging.getLogger("kg.db")
neo4j_logger.setLevel(logging.INFO)
if not neo4j_logger.hasHandlers():
    # 文件日志
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    neo4j_logger.addHandler(handler)

class Neo4jGraphDBEntity:
    """
    增强版Neo4j数据库管理器
    支持单例模式，支持多线程安全
    """
    
    # 单例模式：类级别共享的连接
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, uri=None, user=None, password=None):
        """
        单例构造方法
        仅第一次会创建实例，其余返回同一实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # 双重检查锁（Double-Checked Locking）
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, uri: str = "", user: str = "", password: str = ""):
        """初始化数据库连接（实例化模式）"""
        if not (uri and user and password):
            raise ValueError("uri, user, password 不能为空")

        if self._initialized:
            return
        
        self.uri = uri
        self.user = user
        self.password = password

        self.driver = None

        self._connect()
        self._initialized = True
    

    def _connect(self):
        """建立数据库连接"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            self._log("Neo4j连接成功")
        except Exception as e:
            self._log(f"Neo4j连接失败: {e}", level="ERROR")
            raise
    
    def _log(self, msg, level="INFO"):
        """记录日志"""
        if level == "ERROR":
            neo4j_logger.error(msg)
        else:
            neo4j_logger.info(msg)
    
    def run_query(self, query: Any, parameters: dict = {}):
        """
        执行Cypher查询
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            if not self.driver:
                raise ValueError("未初始化数据库连接")

            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                results_list = list(result)
                
            # 记录日志
            pretty_cql = self.fill_cypher_params(query, parameters or {})
            self._log(f"查询执行成功\nCypher: {pretty_cql}")
            
            return results_list
        except Exception as e:
            pretty_cql = self.fill_cypher_params(query, parameters or {})
            self._log(f"查询执行失败: {e}\nCypher: {pretty_cql}", level="ERROR")
            raise e

    def fill_cypher_params(self, query, parameters):
        """把CQL里的 $param 替换为实际参数值，仅日志用，不建议实际用作查询"""
        if not parameters:
            return query
        def replacer(match):
            key = match.group(1)
            value = parameters.get(key)
            # 字符串加引号，None/null处理，其他原样
            if value is None:
                return "null"
            elif isinstance(value, str):
                return f"'{value}'"
            else:
                return str(value)
        # 匹配 $xxx
        return re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', replacer, query)
    
    # ========== 实体操作方法 ==========
    
    def create_node(self, label: str, properties: dict):
        """
        创建节点
        
        Args:
            label: 节点标签
            properties: 节点属性
            
        Returns:
            创建结果
        """
        query = f"CREATE (n:{label} $props) RETURN n"
        return self.run_query(query, {"props": properties})
    
    
    def find_nodes_by_label(self, label: str, limit: int = 100):
        """根据标签查找节点"""
        query = f"MATCH (n:{label}) RETURN n LIMIT {limit}"
        return self.run_query(query)
    
    
    def delete_node_by_id(self, node_id: str):
        """根据节点ID删除节点"""
        query = "MATCH (n) WHERE elementId(n) = $id DETACH DELETE n"
        return self.run_query(query, {"id": node_id})
    
    def delete_all(self):
        """删除所有节点和关系（慎用！）"""
        query = "MATCH (n) DETACH DELETE n"
        result = self.run_query(query)
        self._log("所有节点和关系已删除")
        return result
    
    def get_node_count(self):
        """获取节点数量"""
        query = "MATCH (n) RETURN count(n) as node_count"
        result = self.run_query(query)
        return result[0]["node_count"] if result else 0
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
            self._log("Neo4j连接已关闭")
    
    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()
    

    def test_connection(self):
        self._log("测试数据库连接")
        try:
            if not self.driver:
                raise ValueError("未初始化数据库连接")
            with self.driver.session() as session:
                session.run("RETURN 1")
            self._log("Neo4j连接正常")
            return True
        except Exception as e:
            self._log(f"Neo4j连接测试失败: {e}", level="ERROR")
            return False