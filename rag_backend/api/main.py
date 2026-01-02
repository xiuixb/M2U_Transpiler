# backend/api/main.py
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

from rag_backend.api.routers import chatsession_router, user_router, kb_router, chat_router

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LangChain RAG 多轮问答系统", version="1.0")

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或指定前端地址 ["http://localhost:8501"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 全局异常处理 ----
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "error": str(exc)}
    )

# ---- 注册路由 ----
app.include_router(user_router.router)
app.include_router(chatsession_router.router)
app.include_router(kb_router.router)
app.include_router(chat_router.router)


@app.get("/")
def index():
    return {"message": "RAG 多轮问答系统已启动"}


@app.get("/healthz")
def healthz():
    """健康检查端点"""
    return JSONResponse(content={"status": "ok"})


@app.get("/init")
async def init_all():
    """初始化所有数据库表"""
    try:
        from rag_backend.system import RAGChatSystem
        system = RAGChatSystem()
        system.init_db()
        return JSONResponse(content={"status": "success", "message": "所有数据库表初始化完成"})
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "message": f"初始化失败: {str(e)}"}, 
            status_code=500
        )