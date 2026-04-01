
import os
import sys
import json
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from src.domain.config.symbolBase import ParseResult
from src.infrastructure.llm_entity import OpenAILLMEntity
from src.domain.core.llm_flows import MCLPromptBuildFlow
from src.infrastructure.llm_config import llm_config

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class LLMParser:
    """
    大模型解析器
    """
    def load_entity(self, 
                    api_key,
                    # vectorDB_flow: ChromaFlow,
                    prompt_flow: MCLPromptBuildFlow
                    ):
        """加载大模型"""
        self.model = OpenAILLMEntity(api_key=api_key)
        self.prompt_flow = prompt_flow

    def parse_cmd(self, model_name, cmd_name, input_list, batch_size=4):
        """解析大模型推送的文本，每4个项拼接成一次处理，并发请求
        
        Args:
            model_name: 模型名称
            cmd_name: 命令名称
            input_list: 输入列表，每个元素都是字典格式
            
        Returns:
            结构化JSON列表，每个元素对应一个输入项的解析结果
        """
        if not input_list:
            return []
        
        batches = []
        for i in range(0, len(input_list), batch_size):
            batch = input_list[i:i + batch_size]
            batches.append(batch)
        
        print(f"总共 {len(input_list)} 个项，分为 {len(batches)} 个批次，每批次 ≤ {batch_size} 个项")
        
        # 使用线程池并发处理各个批次
        # 🚀 激进配置：使用更高的并发数量，充分利用API性能
        max_concurrent = min(10, len(batches))  # 激进配置：最多10个并发批次
        batch_results = [None] * len(batches)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # 创建带重试的future任务
            batch_futures = []
            for i, batch in enumerate(batches):
                future = executor.submit(self._parse_batch_with_json_retry, model_name, cmd_name, batch, i)
                batch_futures.append((i, future))
            
            # 收集所有批次的结果（按批次顺序）
            for batch_index, future in batch_futures:
                try:
                    result = future.result(timeout=60)  # 60秒超时，包含重试时间
                    batch_results[batch_index] = result
                    
                    # 添加时间戳
                    completion_time = time.strftime('%H:%M:%S', time.localtime())
                    print(f"[info] LLM批次: ✅ [{completion_time}] 批次 {batch_index + 1}/{len(batches)} 完成")
                except Exception as e:
                    error_time = time.strftime('%H:%M:%S', time.localtime())
                    print(f"[ERROR] LLM批次: ❌ [{error_time}] 解析批次 {batch_index + 1} 时发生错误: {e}")
                    batch_results[batch_index] = None
        
        # 合并所有批次的JSON结果
        merged_results = []
        for batch_result in batch_results:
            if batch_result and isinstance(batch_result, list):
                merged_results.extend(batch_result)
        
        print(f"成功合并得到 {len(merged_results)} 个结构化结果项")
        return merged_results
    
    def _parse_batch_with_retry(self, model_name, cmd_name, batch, batch_index, max_retries=3):
        """解析一个批次，支持重试机制
        
        Args:
            model_name: 模型名称
            cmd_name: 命令名称
            batch: 一个批次的输入列表
            batch_index: 批次索引（用于日志）
            max_retries: 最大重试次数
            
        Returns:
            该批次的解析结果字符串，失败时返回None
        """
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    wait_time = min(2 ** attempt, 10)  # 指数退避，最多10秒
                    retry_time = time.strftime('%H:%M:%S', time.localtime())
                    print(f"[info] LLM重试: 🔄 [{retry_time}] 批次 {batch_index + 1} 第 {attempt} 次重试，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                
                result = self.parse(model_name, cmd_name, batch)
                
                if result and result.strip():
                    return result
                elif attempt < max_retries:
                    print(f"批次 {batch_index + 1} 返回空结果，准备重试...")
                    continue
                    
            except Exception as e:
                error_msg = str(e).lower()
                # 检查是否是API限制相关的错误
                is_rate_limit_error = any(keyword in error_msg for keyword in [
                    'rate limit', 'too many requests', 'concurrent limit', 
                    'quota', 'throttle', 'busy', 'overloaded'
                ])
                
                if attempt < max_retries:
                    if is_rate_limit_error:
                        wait_time = min(5 * (attempt + 1), 30)  # API限制时等待更长时间
                        print(f"批次 {batch_index + 1} 遇到API限制，等待 {wait_time} 秒后重试...")
                    else:
                        print(f"批次 {batch_index + 1} 处理出错: {e}，准备重试...")
                else:
                    print(f"批次 {batch_index + 1} 重试 {max_retries} 次后仍然失败: {e}")
                    
        return None
    
    def _parse_batch_with_json_retry(self, model_name, cmd_name, batch, batch_index, max_retries=3):
        """解析一个批次，支持重试机制，返回JSON对象
        
        Args:
            model_name: 模型名称
            cmd_name: 命令名称
            batch: 一个批次的输入列表
            batch_index: 批次索引（用于日志）
            max_retries: 最大重试次数
            
        Returns:
            该批次的解析结果JSON列表，失败时返回None
        """
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    wait_time = min(2 ** attempt, 10)  # 指数退避，最多10秒
                    retry_time = time.strftime('%H:%M:%S', time.localtime())
                    print(f"[info] LLM重试JSON: 🔄 [{retry_time}] 批次 {batch_index + 1} 第 {attempt} 次重试，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                
                raw_result = self.parse(model_name, cmd_name, batch)
                
                if raw_result and raw_result.strip():
                    json_result = self._parse_json_result(raw_result)
                    if json_result:
                        # 后处理：为每个结果添加必要字段
                        processed_result = self._post_process_llm_results(json_result, batch)
                        return processed_result
                    elif attempt < max_retries:
                        print(f"批次 {batch_index + 1} JSON解析失败，准备重试...")
                        continue
                
            except Exception as e:
                error_msg = str(e).lower()
                is_rate_limit_error = any(keyword in error_msg for keyword in [
                    'rate limit', 'too many requests', 'concurrent limit', 
                    'quota', 'throttle', 'busy', 'overloaded'
                ])
                
                if attempt < max_retries:
                    if is_rate_limit_error:
                        wait_time = min(5 * (attempt + 1), 30)
                        print(f"批次 {batch_index + 1} 遇到API限制，等待 {wait_time} 秒后重试...")
                    else:
                        print(f"批次 {batch_index + 1} 处理出错: {e}，准备重试...")
                else:
                    print(f"批次 {batch_index + 1} 重试 {max_retries} 次后仍然失败: {e}")
                    
        return None
    
    def _post_process_llm_results(self, llm_results, original_batch):
        """后处理LLM解析结果，添加必要字段和错误处理
        
        Args:
            llm_results: LLM返回的JSON结果列表
            original_batch: 原始输入批次
            
        Returns:
            处理后的结果列表
        """
        if not isinstance(llm_results, list):
            return []
        
        # 创建原始项目的映射
        original_by_lineno = {}
        for item in original_batch:
            lineno = item.get("lineno", "0")
            original_by_lineno[str(lineno)] = item
        
        processed_results = []
        
        for result in llm_results:
            if not isinstance(result, dict):
                continue
            
            # 获取行号
            lineno = str(result.get("lineno", "0"))
            original_item = original_by_lineno.get(lineno)
            
            # 添加text字段（从原始输入获取）
            if original_item and "text" not in result:
                result["text"] = original_item.get("text", "")
            
            # 统一errors字段为字符串类型
            errors = result.get("errors", "no")
            if isinstance(errors, list):
                if not errors or (len(errors) == 1 and errors[0] == "no"):
                    result["errors"] = "no"
                else:
                    result["errors"] = "; ".join(str(e) for e in errors)
            elif errors is None:
                result["errors"] = "no"
            else:
                result["errors"] = str(errors)
            
            # 添加ok字段
            has_payload = bool(result.get("payload"))
            no_errors = result["errors"] == "no"
            result["ok"] = has_payload and no_errors
            
            processed_results.append(result)
        
        return processed_results
    
    def _parse_json_result(self, raw_result):
        """解析LLM返回的JSON结果
        
        Args:
            raw_result: LLM返回的原始字符串
            
        Returns:
            解析后的JSON列表或None
        """
        try:
            # 直接尝试解析JSON
            json_obj = json.loads(raw_result.strip())
            
            # 确保返回的是列表格式
            if isinstance(json_obj, list):
                return json_obj
            else:
                # 如果不是列表，包装成列表
                return [json_obj]
                
        except json.JSONDecodeError as e:
            # JSON解析失败，尝试提取JSON部分
            print(f"JSON解析失败，尝试提取JSON部分: {e}")
            
            # 尝试提取第一个完整的JSON对象
            json_str = self._extract_json_object(raw_result)
            if json_str:
                try:
                    json_obj = json.loads(json_str)
                    if isinstance(json_obj, list):
                        return json_obj
                    else:
                        return [json_obj]
                except:
                    pass
            
            print(f"无法解析JSON结果: {raw_result[:200]}...")
            return None
    
    def _extract_json_object(self, text):
        """从文本中提取第一个完整的JSON对象
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            提取的JSON字符串或None
        """
        text = text.strip()
        
        # 查找第一个 { 或 [
        start_char = None
        start_index = -1
        
        for i, char in enumerate(text):
            if char in '{[':
                start_char = char
                start_index = i
                break
        
        if start_char is None:
            return None
        
        # 找到匹配的结束字符
        end_char = '}' if start_char == '{' else ']'
        stack = []
        
        for i in range(start_index, len(text)):
            char = text[i]
            
            if char == start_char:
                stack.append(char)
            elif char == end_char:
                if stack:
                    stack.pop()
                    if not stack:  # 找到匹配的结束位置
                        return text[start_index:i+1]
            
        return None
    
    def _parse_with_retry(self, model_name, cmd_name, input_list, max_retries=2):
        """单个请求的重试包装"""
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    wait_time = min(2 ** attempt, 5)
                    time.sleep(wait_time)
                
                result = self.parse(model_name, cmd_name, input_list)
                if result and result.strip():
                    return result
            except Exception as e:
                if attempt == max_retries:
                    print(f"单批次处理失败: {e}")
                    return None
        return None
    
    def _parse_single_item(self, model_name, cmd_name, single_item_list):
        """解析单个输入项的内部方法
        
        Args:
            model_name: 模型名称
            cmd_name: 命令名称
            single_item_list: 包含单个项目的列表
            
        Returns:
            解析结果字符串
        """
        return self.parse(model_name, cmd_name, single_item_list)


    def parse(self, model_name, cmd_name, input_list):
        """解析大模型推送的文本，list不能超过10个"""
        # 1. 从向量数据库检索相关文档
        #docs_list = self.vectorDB_flow.similarity_search(user_query, k=5)
        
        # 2. 构建带上下文的提示词
        prompt = self.prompt_flow.build_parse_prompt("parse", cmd_name, input_list)
        
        # 3. 构建LangChain消息格式（使用传入的对话历史）
        messages = [
            {
                "role": "system",
                "content": "这是一个文本处理任务，你需要根据用户的指令处理文本，不要有任何解释和多余字符，方便后续处理直接输出json对象"
            },
            {
                "role": "user",
                "content": prompt, 
            },
        ]
        
        # 4. 调用LLM获取回答
        ai_response = self.model.chat(model_name, messages)
        print("[LLM] 输入:", input_list)
        # print("[LLM] 输出:", ai_response.choices[0].message.content)  # type: ignore

        return ai_response.choices[0].message.content  # type: ignore


if __name__ == "__main__":
    llmparser = LLMParser()
    
    llmparser.load_entity(api_key=llm_config.api_key, prompt_flow=MCLPromptBuildFlow())
    
    # 测试原始parse方法
    print("=== 测试parse方法 ===")
    result = [#parser.parse("qwen-plus", "ASSIGN", [
        {"lineno": "4", "command": "ASSIGN", "text": "VOLTAGE_RISE_TIME = 2 NANOSECONDS ;"},
        {"lineno": "5", "command": "ASSIGN", "text": "VOLTAGE_MAX = 1.0 MEGAVOLTS ;"}
        ]
    print(result)
    
    # 测试新的parse_cmd方法（每6项并发处理，返回列表）
    print("\n=== 测试parse_cmd方法（每6项并发处理，返回列表） ===")
    large_input_list = [
        {"lineno": "4", "command": "ASSIGN", "text": "VOLTAGE_RISE_TIME = 2 NANOSECONDS ;"},
        {"lineno": "5", "command": "ASSIGN", "text": "VOLTAGE_MAX = 1.0 MEGAVOLTS ;"},
        {"lineno": "6", "command": "ASSIGN", "text": "CURRENT_MAX = 500 MILLIAMPS ;"},
        {"lineno": "7", "command": "ASSIGN", "text": "FREQUENCY = 100 MEGAHERTZ ;"},
        {"lineno": "8", "command": "ASSIGN", "text": "POWER_RATING = 50 WATTS ;"},
        {"lineno": "9", "command": "ASSIGN", "text": "RESISTANCE = 100 OHMS ;"},  # 第6个项
        {"lineno": "10", "command": "ASSIGN", "text": "CAPACITANCE = 10 MICROFARADS ;"},
        {"lineno": "11", "command": "ASSIGN", "text": "INDUCTANCE = 1 MILLIHENRY ;"},
        {"lineno": "12", "command": "ASSIGN", "text": "IMPEDANCE = 75 OHMS ;"},
        {"lineno": "13", "command": "ASSIGN", "text": "BANDWIDTH = 20 MEGAHERTZ ;"},
        {"lineno": "14", "command": "ASSIGN", "text": "GAIN = 20 DECIBELS ;"},
        {"lineno": "15", "command": "ASSIGN", "text": "NOISE_FIGURE = 3 DECIBELS ;"},  # 第12个项
        {"lineno": "16", "command": "ASSIGN", "text": "TEMPERATURE = 25 CELSIUS ;"},
        {"lineno": "17", "command": "ASSIGN", "text": "HUMIDITY = 60 PERCENT ;"}
    ]
    
    print(f"输入列表长度: {len(large_input_list)}")
    result_list = llmparser.parse_cmd("qwen-plus", "ASSIGN", large_input_list, batch_size=7)
    print(f"\n返回结果列表长度: {len(result_list)}")
    print("合并后的所有结果列表:")
    print(json.dumps(result_list, indent=2, ensure_ascii=False))  # 这就是包含所有输入项解析结果的统一列表
    