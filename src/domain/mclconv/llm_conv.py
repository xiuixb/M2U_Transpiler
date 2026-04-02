import os
import sys
import json
import time
from datetime import datetime
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

from src.domain.config.cmd_dic import MCL2MID_CmdDict
from src.infrastructure.llm_entity import OpenAILLMEntity
from src.domain.core.llm_flows import MCLPromptBuildFlow
from src.domain.config.prompt import mcl2mid_mclcontext_dict, mcl2mid_midcontext_dict, mcl2mid_json_dict


class LLMConv:
    """
     LLM转换类,接收数据列表后，按照一定算法分组并发执行LLM转换，并汇总数据、返回转换结果
    """
    def load_entity(self, 
                    mcl2mid_dict: MCL2MID_CmdDict,
                    api_key,
                    prompt_flow: MCLPromptBuildFlow = None,
                    concurrent = 10                    
                    ):
        """加载大模型和提示词构造器"""
        self.model = OpenAILLMEntity(api_key=api_key)
        self.concurrent_num = concurrent
        self.mcl2mid_dict = mcl2mid_dict
        self.MID_dict = self.mcl2mid_dict.MID_dict

        if prompt_flow:
            self.prompt_flow = prompt_flow

        self.llm_io_log = ""

    def process_list(self):
        processed_mcl_list = {}
        for mcl_type in self.mcl_list.keys():
            if self.mcl_list[mcl_type]:
                print(f"[debug] 处理MCL类型: {mcl_type}")
            if self.mcl_list[mcl_type]:
                processed_mcl_list[mcl_type] = self.mcl_list[mcl_type]

        return processed_mcl_list

    def llmconv_mcl2mid(self, 
                    mcl_list: Dict[str, List[dict]],
                    model_name, 
                    llmconv_debug=False,
                    batch_size=4,
                    result_wait_time=60):
        """
        这里是llmconv_mcl2mid的入口方法，用于传入MCL列表，并发转换，汇总结果，返回LLM转换的结果
        返回llm_results: List[dict]
        """
        print(f"\n[debug] 开始llmconv_mcl2mid，llmconv_debug={llmconv_debug}")
        self.mcl_list = mcl_list
        self.mcl_list = self.process_list()

        if not self.mcl_list:
            return []
        
        # 对每个类型的MCL列表进行分组
        batches = []
        for mcl_type, mcl_items in self.mcl_list.items():
            for i in range(0, len(mcl_items), batch_size):
                batch = mcl_items[i:i + batch_size]
                batches.append(batch)
        
        print(f"\n[debug] 总共 {len(mcl_items)} 个项，分为 {len(batches)} 个批次，每批次 ≤ {batch_size} 个项")

        start_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[info] 开始时间 {start_time}")
        # 使用线程池并发处理各个批次
        # 提高并发数量，尽量利用 API 吞吐
        max_concurrent = min(self.concurrent_num, len(batches))  # 并发批次计算
        
        batch_results = [None] * len(batches)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # 创建带重试的future任务
            batch_futures = []
            for i, batch in enumerate(batches):
                future = executor.submit(self._mclconv_batch_with_json_retry, model_name, batch, i, llmconv_debug)
                batch_futures.append((i, future))
            
            # 收集所有批次的结果（按批次顺序）
            for batch_index, future in batch_futures:
                try:
                    result = future.result(timeout=result_wait_time)  # 等待结果，超时时间为result_wait_time秒
                    #print(f"[info] 批次 {batch_index + 1} 结果: {result}")
                    batch_results[batch_index] = result
                    
                    # 添加时间戳
                    completion_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    print(f"\n[info] LLM批次: [done] [{completion_time}] 批次 {batch_index + 1}/{len(batches)} 完成")
                except Exception as e:
                    import traceback
                    error_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    print(f"[ERROR] LLM批次: [failed] [{error_time}] 解析批次 {batch_index + 1} 时发生错误: {e}")
                    print(f"[ERROR] 错误详情: {traceback.format_exc()}")
                    batch_results[batch_index] = None
        print(f"[debug] 处理批次结果:\n {batch_results}")
        # 合并所有批次的JSON结果
        merged_results = []
        for batch_result in batch_results:
            if batch_result and isinstance(batch_result, list):
                merged_results.extend(batch_result)
        
        print(f"成功合并得到 {len(merged_results)} 个结构化结果项")
        #print(merged_results)
        #print(json.dumps(merged_results, ensure_ascii=False, indent=2))

        with open("data\\BWO\\workdir\\llm_io_log.txt", "w", encoding="utf-8") as f:
            f.write(self.llm_io_log)

        return merged_results
    
    
    def _mclconv_batch_with_json_retry(self, model_name, batch, batch_index, llmconv_debug, max_retries=3):
        """处理一个批次的转换，支持重试机制，返回JSON对象
        
        Args:
            model_name: 模型名称
            batch: 一个批次的输入列表
            batch_index: 批次索引（用于日志）
            max_retries: 最大重试次数
            
        Returns:
            该批次的解析结果JSON列表，失败时返回None
        """
        #print(f"[debug] 处理批次 {batch_index + 1}，\n {batch[0]}\n")
        print(f"\n[debug] 处理批次 {batch_index + 1}, llmconv_debug={llmconv_debug}")
        cmd_type = batch[0]["mcl_type"]

        if not cmd_type:
            return None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    wait_time = min(2 ** attempt, 10)  # 指数退避，最多10秒
                    retry_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    print(f"[info] LLM重试JSON: [retry] [{retry_time}] 批次 {batch_index + 1} 第 {attempt} 次重试，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                
                raw_result = self._conv(model_name, cmd_type, batch, llmconv_debug)
                print(f"\n[debug] 批次{batch_index + 1} LLM 输出后处理 llm_debug={llmconv_debug}")

                if llmconv_debug:
                    return raw_result
                else:
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
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"批次 {batch_index + 1} 重试 {max_retries} 次后仍然失败: {e}")
                    
        return None
    
    def _conv(self, model_name, cmd_name, input_list, llmconv_debug=False):
        """
        通过input_list构造prompt，调用LLM获取回答
        还没改，要把src\\core_symbol\\muti_flows\\llm_conv\\mcl2mid_sTconv.py中的逻辑拿过来
        """
        
        # 读取list中的相关参数
        record0 = input_list[0]
        mcl_type = record0["mcl_type"]
        mcl_type_single = record0["mcl_type"].split()[0]

        mcl_cmd_text_list = []
        mcl_payload_list = []
        for record in input_list:
            mcl_cmd_text_list.append(record["mcl_cmd_text"])
            mcl_payload_list.append(record["mcl_payload"])


        # 下面是RAG思路标准流程
        # 1. 检索相关文档
        # 向量数据库检索
        # docs_list = self.vectorDB_flow.similarity_search(user_query, k=5)

        # 字典查询
        ## 查询对应的中间符号表元素列表
        mid_elements = self.MID_dict[mcl_type_single]

        ## mcl命令背景知识
        mcl_cmd_context = mcl2mid_mclcontext_dict[mcl_type_single]    
        
        mid_cmd_context = ""
        ## mid符号参数背景知识
        for mid_element in mid_elements:
            mid_cmd_context += f"### {mid_element}背景知识:\n" + mcl2mid_midcontext_dict[mid_element] + "\n"    

        ## mcl2mid 输出json示例
        mcl2mid_json = mcl2mid_json_dict[mcl_type]  

        
        # 2. 构建带上下文的提示词
        prompt = self.prompt_flow.build_mcl2mid_prompt(        
                mcl_type,
                mid_elements,
                mcl_cmd_text_list,
                mcl_cmd_context,
                mid_cmd_context,
                mcl2mid_json,
                mcl_payload_list                
                )
        
        if not llmconv_debug:
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
            
            # 记录LLM输入输出
            self.llm_io_log = self.llm_io_log + f"\n{prompt}\n{ai_response.choices[0].message.content}"

            return ai_response.choices[0].message.content  # type: ignore
        else:

            test_txt = {
                "sys_type": "test",
                "value": {"txt":prompt}
            }
            self.llm_io_log = self.llm_io_log + f"\n{prompt}\n\n\n"
            
            return test_txt

    def _post_process_llm_results(self, llm_results, original_batch):
        """
        后处理LLM转换结果，添加必要字段和错误处理
        还没改
        """
        # print(f"[debug] 原始LLM输入: {original_batch}")
        # print(f"[debug] 原始LLM结果: {llm_results}")

        if not isinstance(llm_results, dict):
            return []

        processed_llm_results = []
        for sys_type, mid_items in llm_results.items():
            for mid_item in mid_items:
                processed_llm_results.append({
                    "sys_type": sys_type,
                    "value": mid_item
                })
        
        return processed_llm_results
    
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
            
            # 确保返回的是字典格式（可能要改）
            if isinstance(json_obj, dict):
                return json_obj
            else:
                # 如果不是列表，包装成列表
                raise ValueError(f"LLM返回的JSON结果不是字典格式: {json_obj}")
                
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
    
