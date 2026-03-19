# backend/api/routers/chat.py

from fastapi import APIRouter, WebSocket, Form, WebSocketException, Depends
from fastapi.responses import JSONResponse

import json
import asyncio
from rag_backend.api.deps.auth import get_current_user
from rag_backend.system import RAGChatSystem

from fastapi.exceptions import HTTPException

router = APIRouter(prefix="/api/chat", tags=["Chat"])
rag_system = RAGChatSystem()


@router.websocket("/stream")
async def chat_stream(ws: WebSocket):
    """流式问答接口（WebSocket）"""
    try:
        await ws.accept()
        
        # 接收参数并进行验证
        try:
            params = await ws.receive_json()
            user_name = params.get("user_name")
            chat_id = params.get("chat_id") 
            prompt = params.get("prompt")
            use_rag = params.get("use_rag", False)
            
            if not all([user_name, chat_id, prompt]):
                await ws.send_text(json.dumps({"error": "缺少必要参数: user_name, chat_id, prompt"}))
                await ws.close(code=1002, reason="参数错误")
                return
                
        except json.JSONDecodeError:
            await ws.send_text(json.dumps({"error": "无效的JSON格式"}))
            await ws.close(code=1002, reason="JSON解析错误")
            return
        except Exception as e:
            await ws.send_text(json.dumps({"error": f"参数解析错误: {str(e)}"}))
            await ws.close(code=1002, reason="参数错误")
            return
        
        # 处理流式对话
        try:
            full_response = ""
            async for chunk in rag_system.chat_stream(user_name, chat_id, prompt, use_rag=use_rag):
                if isinstance(chunk, dict) and chunk.get("event") == "end":
                    # 发送结束事件，包含完整响应
                    chunk["full_response"] = full_response
                    await ws.send_text(json.dumps(chunk))
                else:
                    # 发送文本片段，使用统一的JSON格式
                    text_chunk = chunk if isinstance(chunk, str) else str(chunk)
                    full_response += text_chunk
                    response_data = {
                        "event": "chunk",
                        "text": text_chunk,
                        "timestamp": ""
                    }
                    await ws.send_text(json.dumps(response_data))
                    
        except Exception as e:
            # 捕获对话过程中的异常
            import traceback
            error_trace = traceback.format_exc()
            error_msg = f"对话处理错误: {str(e)}\n详细错误路径:\n{error_trace}"
            await ws.send_text(json.dumps({"error": error_msg, "event": "error"}))
            
    except WebSocketException as ws_error:
        # WebSocket特定异常
        print(f"WebSocket异常: {ws_error}")
        try:
            await ws.close(code=ws_error.code if hasattr(ws_error, 'code') else 1011, 
                          reason=str(ws_error))
        except:
            pass  # 如果连接已经关闭，忽略异常
    except Exception as e:
        # 其他未预期的异常
        print(f"未预期的错误: {e}")
        try:
            await ws.send_text(json.dumps({"error": "服务器内部错误", "event": "error"}))
            await ws.close(code=1011, reason="内部服务器错误")
        except:
            pass  # 如果连接已经关闭，忽略异常
    finally:
        # 确保连接被正确关闭
        try:
            if not ws.client_state.DISCONNECTED:
                await ws.close()
        except:
            pass


@router.post("/message")
async def chat_message(
    prompt: str = Form(...),
    chat_id: str = Form(...),
    user_name: str = Depends(get_current_user)
):
    """同步问答接口"""
    try:
        # 调用RAG系统进行聊天
        response_text = await asyncio.to_thread(
            rag_system.chat, user_name, chat_id, prompt
        )
        
        return JSONResponse({
            "response": response_text,
            "chat_id": chat_id
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")


@router.get("/history")
async def get_chat_history(
    chat_id: str,
    user_name: str = Depends(get_current_user)
):
    """获取聊天历史记录"""
    try:
        # 调用RAG系统获取聊天历史
        history = await asyncio.to_thread(
            rag_system.get_chat_history, user_name, chat_id
        )
        
        return JSONResponse({
            "history": history,
            "chat_id": chat_id
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取聊天历史失败: {str(e)}")