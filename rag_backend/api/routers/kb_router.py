# backend/api/routers/kb_router.py
from fastapi import APIRouter, UploadFile, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import os
from pydantic import BaseModel

from rag_backend.system import RAGChatSystem
from rag_backend.api.deps.auth import get_current_user

router = APIRouter(prefix="/api/kb", tags=["KnowledgeBase"])
rag_system = RAGChatSystem()


UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ManualContent(BaseModel):
    content: str


@router.post("/upload")
async def upload_kb(file: UploadFile, user_name: str = Depends(get_current_user)):
    """上传文件 → 入库到 Chroma 向量数据库"""
    try:
        # 验证文件类型
        allowed_extensions = {'.txt', '.pdf', '.doc', '.docx', '.md'}
        file_ext = os.path.splitext(file.filename)[1].lower() # type: ignore
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file_ext}。支持的格式: {', '.join(allowed_extensions)}"
            )
        
        # 验证文件大小 (10MB限制)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, 
                detail="文件大小超过10MB限制"
            )
        
        temp_path = os.path.join(UPLOAD_DIR, file.filename)  # type: ignore
        with open(temp_path, "wb") as f:
            f.write(contents)

        result = await rag_system.a_ingest_kb(temp_path, {"uploader": user_name})
        
        # 清理临时文件
        try:
            os.remove(temp_path)
        except:
            pass
            
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/search")
async def search_kb(query: str, top_k: int = 5, user_name: str = Depends(get_current_user)):
    """知识检索接口"""
    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        if top_k <= 0 or top_k > 20:
            raise HTTPException(status_code=400, detail="top_k参数必须在1-20之间")
            
        results = await asyncio.to_thread(rag_system.search_kb, query, top_k)
        return JSONResponse({"results": results})
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识检索失败: {str(e)}")
    

@router.post("/add_manual")
async def add_manual(manual_content: ManualContent, user_name: str = Depends(get_current_user)):
    """手动录入知识片段（直接入向量数据库）"""
    try:
        from langchain_core.documents import Document
        rag_system = RAGChatSystem()

        # 调试输出：打印接收到的内容，验证缩进格式
        print("=== 后端接收到的内容调试信息 ===")
        print(f"接收到的内容长度: {len(manual_content.content)} 字符")
        print(f"接收到的内容行数: {len(manual_content.content.splitlines())} 行")
        print("接收到的内容前500字符（带格式）:")
        print(repr(manual_content.content))
        print("\n接收到的内容前10行:")
        for i, line in enumerate(manual_content.content.splitlines()):
            print(f"行{i+1:2d}: {repr(line)}")
        print("=== 调试信息结束 ===")

        # 构建文档对象，保持原始内容格式
        doc = Document(page_content=manual_content.content, metadata={"source": "manual", "uploader": user_name})

        # 存入 Chroma
        rag_system.vector_flow.add_documents([doc])
        return JSONResponse({"status": "success", "message": "知识片段已保存"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存知识片段失败: {str(e)}")
    

@router.get("/list")
async def list_all_docs(user_name: str = Depends(get_current_user)):
    """列出当前知识库的所有文档"""
    try:
        rag_system = RAGChatSystem()
        docs = rag_system.vector_flow.db.get_all_docs()
        return JSONResponse({"docs": docs, "count": len(docs)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")


@router.delete("/delete/{doc_id}")
async def delete_doc(doc_id: str, user_name: str = Depends(get_current_user)):
    """根据ID删除指定文档"""
    try:
        rag_system = RAGChatSystem()
        rag_system.vector_flow.delete_documents([doc_id])
        return JSONResponse({"status": "success", "message": f"文档 {doc_id} 已删除"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.post("/clear")
async def clear_all(user_name: str = Depends(get_current_user)):
    """清空整个向量数据库"""
    try:
        rag_system = RAGChatSystem()
        # 获取所有文档 ID 并删除
        docs = rag_system.vector_flow.db.get_all_docs()
        ids = [d["id"] for d in docs]
        if ids:
            rag_system.vector_flow.delete_documents(ids)
        return JSONResponse({"status": "success", "message": f"已清空 {len(ids)} 条知识片段"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空知识库失败: {str(e)}")