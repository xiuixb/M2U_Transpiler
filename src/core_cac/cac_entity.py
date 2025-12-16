# core/entities.py

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

from openai.types.chat import ChatCompletion
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

import os
import sys
import json
from openai import OpenAI

# 自动找到项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

class LCLLMEntity:
    """大模型实体（封装阿里百炼API，兼容OpenAI接口）"""
    def __init__(self, model_name, api_key, system_prompt="You are a helpful assistant."):
        self.model = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            streaming=True,
        )
        self.system_prompt = system_prompt

    def chat(self, messages):
        """messages为LangChain格式的ChatMessage列表"""
        return self.model.invoke(messages)
    
    def chat_stream(self, messages):
        """流式调用：返回同步生成器，每次 yield 一个文本片段"""
        # LangChain的stream方法返回同步生成器
        stream = self.model.stream(messages)
        
        # 直接迭代同步生成器
        for chunk in stream:
            if chunk.content:
                yield chunk.content

class OpenAILLMEntity():
    """OpenAI大模型实体"""
    def __init__(self, api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def create_completion(self, model_name, messages, stream=False, **kwargs):
        """创建模型完成"""
        return self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=stream, 
            response_format={"type": "json_object"},
            **kwargs
        )
        
    
    def chat(self, model_name, messages, **kwargs):
        """调用模型进行聊天"""
        return self.create_completion(model_name, messages, stream=False, **kwargs)

    def chat_stream(self, model_name, messages, **kwargs):
        """流式调用：返回同步生成器，每次 yield 一个文本片段"""
        stream = self.create_completion(model_name, messages, stream=True, **kwargs)
        for chunk in stream:
            if chunk.choices[0].delta.content:          # type: ignore
                yield chunk.choices[0].delta.content    # type: ignore

class EmbeddingEntity:
    """嵌入模型实体（封装 DashScope 嵌入模型）"""
    def __init__(self, model_name, api_key):
        self.model = DashScopeEmbeddings(
            model=model_name,
            dashscope_api_key=api_key
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)
    
    def embed_query(self, text: str) -> list[float]:
        return self.model.embed_query(text)
