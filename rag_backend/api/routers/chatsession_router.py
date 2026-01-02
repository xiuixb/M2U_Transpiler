# backend/api/routers/chatsession_router.py
from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse
import asyncio
from rag_backend.system import RAGChatSystem
from rag_backend.api.deps.auth import get_current_user
from fastapi.exceptions import HTTPException


router = APIRouter(prefix="/api/chatsession", tags=["ChatSession"])
rag_system = RAGChatSystem()


@router.post("/create_session")
async def create_chat_session(
    title: str = Form(...),
    chat_type: str = Form("rag"),
    user_name: str = Depends(get_current_user),
):
    """创建新的聊天会话"""
    chat_id = await asyncio.to_thread(rag_system.create_chat_session, user_name, title, chat_type)
    return JSONResponse({"chat_id": chat_id, "message": "会话已创建"})


@router.get("/sessions")
async def list_sessions(user_name: str = Depends(get_current_user)):
    """列出用户的所有会话"""
    sessions = await asyncio.to_thread(rag_system.list_chat_sessions, user_name)
    return JSONResponse({"sessions": sessions})


@router.post("/clear_session")
async def delete_chat_session(chat_id: str = Form(...), user_name: str = Depends(get_current_user)):
    """删除指定会话"""
    await asyncio.to_thread(rag_system.delete_chat_session, user_name, chat_id)
    return JSONResponse({"status": "success"})


@router.get("/history/{chat_id}")
async def get_chat_history(chat_id: str, user_name: str = Depends(get_current_user)):
    """获取指定会话的聊天历史"""
    try:
        history = await asyncio.to_thread(rag_system.get_chat_history, user_name, chat_id)
        return JSONResponse({
            "history": history,
            "chat_id": chat_id
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取聊天历史失败: {str(e)}")


@router.post("/rename_session")
async def rename_chat_session(
    chat_id: str = Form(...),
    new_title: str = Form(...),
    user_name: str = Depends(get_current_user),
):
    """重命名指定会话"""
    try:
        await asyncio.to_thread(rag_system.rename_chat_session, user_name, chat_id, new_title)
        return JSONResponse({"status": "success", "message": "会话已重命名"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重命名失败: {str(e)}")