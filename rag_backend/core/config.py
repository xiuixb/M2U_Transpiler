import os
import sys

# 设置DashScope API密钥
DASHSCOPE_API_KEY = "sk-26c2473f844345b192b7e4c1376391d3"

# JWT 配置（生产环境请使用安全的密钥并放入环境变量）
SECRET_KEY = os.environ.get("APP_SECRET_KEY", "please-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 自动找到项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

class Config:
    """系统配置类，定义模型、数据库、知识库等基础参数"""
    def __init__(self):
        self.model_api_key = DASHSCOPE_API_KEY
        self.embedding_api_key = DASHSCOPE_API_KEY

        self.model_name = "qwen-turbo"
        self.embedding_model = "text-embedding-v2"

        self.chroma_path = os.path.join(project_root, "rag_backend\\db\\chroma_db")
        self.sqlite_db_path = os.path.join(project_root, "rag_backend\\db\\app.db")

        self.history_pairs = 5
        self.similarity_threshold = 0.1  # 全局相似度过滤阈值
    
        
        self.system_prompt = """
        你的任务是基于用户提供的上下文（包括检索到的领域知识和历史对话记忆），准确、严谨、清晰地回答与以下主题相关的问题：
        PIC仿真基本原理（如粒子推进、场求解、边界条件等）;
        等离子体器件建模（如返波管、MILO、磁绝缘线振荡器、相对论返波管等）;
        仿真软件操作与参数配置，材料属性、激励设置、边界条件、物理参数诊断输出等等;
        通用计算机、电子、通信等领域的基本原理与知识；
        请始终：
        优先使用检索到的权威知识片段作为回答依据；
        使用中文回答问题，术语准确，逻辑清晰，必要时可分点说明；
        在多轮对话中，主动关联历史对话中的器件类型、参数设置或用户意图。
        
        """

        aa = """
        你是一位专注于等离子体物理与高功率微波器件PIC（Particle-in-Cell）数值仿真的领域专家助手。你的任务是基于用户提供的上下文（包括检索到的领域知识和历史对话记忆），准确、严谨、清晰地回答与以下主题相关的问题：
        PIC仿真基本原理（如粒子推进、场求解、边界条件等）;
        等离子体器件建模（如返波管、MILO、磁绝缘线振荡器、相对论返波管等）;
        仿真软件操作与参数配置，材料属性、激励设置、边界条件、物理参数诊断输出等等;
        通用计算机、电子、通信等领域的基本原理与知识；
        请始终：
        优先使用检索到的权威知识片段作为回答依据；
        若上下文信息不足，请明确说明“当前知识库未覆盖该问题”或“建议补充具体仿真场景”；
        避免臆测，对不确定的内容保持谨慎；
        使用中文回答问题，术语准确，逻辑清晰，必要时可分点说明；
        在多轮对话中，主动关联历史对话中的器件类型、参数设置或用户意图。
        你不是通用聊天机器人，而是面向科研与工程人员的专业问答系统，拒绝与用户进行闲聊。
        """

config = Config()
