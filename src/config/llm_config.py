"""
LLM解析器配置模块
管理LLM解析器的各种配置参数
"""

import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM解析器配置类"""
    
    # 基础配置 - 直接写出参数值
    model_name: str = "qwen-turbo"
    api_key: str = "sk-26c2473f844345b192b7e4c1376391d3"  # 直接配置API密钥
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    

    # 解析配置
    batch_size_limit: int = 10  # 单次批量解析的最大命令数
    enable_batch_parsing: bool = True  # 是否启用批量解析
    enable_fallback: bool = True  # 是否启用回退机制
    
    # 重试配置
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 2.0  # 重试延迟（秒）
    
    # 超时配置
    request_timeout: int = 30  # 请求超时时间（秒）
    
    # 调试配置
    debug_mode: bool = False  # 是否启用调试模式
    log_requests: bool = False  # 是否记录请求日志



class CommandTypeConfig:
    """命令类型配置"""
    
    # 支持批量解析的命令类型
    BATCH_SUPPORTED_COMMANDS = {
        "ASSIGN", "POINT", "LINE", "AREA", 
        "PORT", "EMISSION", "EMIT", "OBSERVE", 
        "FUNCTION", "CONDUCTOR", "INDUCTOR"
    }
    
    # 命令优先级（数字越小优先级越高）
    COMMAND_PRIORITY = {
        "ASSIGN": 1,    # 变量定义优先
        "FUNCTION": 2,  # 函数定义
        "POINT": 3,     # 几何定义
        "LINE": 4,
        "AREA": 5,
        "CONDUCTOR": 6, # 材料定义
        "INDUCTOR": 7,
        "PORT": 8,      # 边界条件
        "EMISSION": 9,
        "EMIT": 10,
        "OBSERVE": 11,  # 观测设置
    }
    



class PromptTemplates:
    """提示词模板"""
    
    # 基础系统提示词
    BASE_SYSTEM_PROMPT = """你是一个专门解析MAGIC MCL命令的专家系统。

你的任务是将MAGIC MCL命令解析为结构化的JSON格式，用于后续的转换处理。

## 输出格式要求：
请严格按照以下JSON格式输出，不要添加任何额外的文字说明：

```json
{
    "command": "命令名称",
    "payload": {
        "参数名1": "参数值1",
        "参数名2": "参数值2"
    },
    "ok": true,
    "errors": []
}
```

## 解析规则：
1. 提取命令名称（第一个单词）
2. 解析所有参数和值
3. 处理单位信息（如果存在）
4. 识别变量引用和表达式
5. 如果解析失败，设置ok为false并在errors中说明原因

请严格按照此格式解析用户提供的MAGIC命令。"""
    

    # 命令特定的提示词

    @classmethod
    def get_system_prompt(cls, command_type: str = None) -> str:
        """获取系统提示词"""
        base_prompt = cls.BASE_SYSTEM_PROMPT
        
        if command_type and command_type in cls.COMMAND_SPECIFIC_PROMPTS:
            specific_prompt = cls.COMMAND_SPECIFIC_PROMPTS[command_type]
            return f"{base_prompt}\n\n## {command_type}命令特定说明：\n{specific_prompt}"
        
        return base_prompt
    
    @classmethod
    def get_batch_prompt_template(cls, command_type: str) -> str:
        """获取批量解析的提示词模板"""
        return f"""请解析以下 {{count}} 条 {command_type} 命令：

{{commands}}

请为每条命令返回一个JSON对象，格式如下：
```json
[
  {{
    "index": 1,
    "command": "{command_type}",
    "payload": {{"参数名": "参数值"}},
    "ok": true,
    "errors": []
  }},
  {{
    "index": 2,
    "command": "{command_type}", 
    "payload": {{"参数名": "参数值"}},
    "ok": true,
    "errors": []
  }}
]
```

注意：
1. index对应命令序号（1, 2, 3...）
2. 所有命令都是{command_type}类型
3. 如果某条命令解析失败，设置ok为false并在errors中说明原因
4. 请严格按照JSON数组格式返回，不要添加其他文字

{cls.COMMAND_SPECIFIC_PROMPTS.get(command_type, "")}"""


# 默认配置实例
llm_config = LLMConfig()
command_config = CommandTypeConfig()
prompt_templates = PromptTemplates()