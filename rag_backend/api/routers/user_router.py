# backend/api/routers/user_router.py
from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import asyncio
from rag_backend.system import RAGChatSystem
from rag_backend.api.deps.auth import create_access_token, get_current_user

router = APIRouter(prefix="/api/user", tags=["User"])
rag_system = RAGChatSystem()


@router.post("/register")
async def register(user_name: str = Form(...), password: str = Form(...)):
    """用户注册"""
    try:
        if not user_name or len(user_name.strip()) < 3:
            raise HTTPException(status_code=400, detail="用户名长度至少3个字符")
        if not password or len(password) < 6:
            raise HTTPException(status_code=400, detail="密码长度至少6个字符")
            
        user_name = await asyncio.to_thread(rag_system.register_user, user_name.strip(), password)
        return JSONResponse({"user_name": user_name, "message": "注册成功"})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/login")
async def login(user_name: str = Form(...), password: str = Form(...)):
    """用户登录"""
    try:
        if not user_name or not password:
            raise HTTPException(status_code=400, detail="用户ID和密码不能为空")
            
        ok = await asyncio.to_thread(rag_system.login_user, user_name, password)
        if not ok:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
            
        token = create_access_token({"sub": user_name})
        return JSONResponse({
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user_name}
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.get("/me")
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    """获取当前用户信息"""
    try:
        user_info = await asyncio.to_thread(rag_system.user_service.get_info, current_user)
        return JSONResponse({
            "user_name": current_user,
            "info": user_info
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")