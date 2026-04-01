"""
==========================
src/domain/config/llm_config.py
==========================
定义了LLM解析器配置，包括：
- LLM配置类
- 命令类型配置类
- 提示词模板类
- 默认配置实例
"""

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
    



# 默认配置实例
llm_config = LLMConfig()
command_config = CommandTypeConfig()