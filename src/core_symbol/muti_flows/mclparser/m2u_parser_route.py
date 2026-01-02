"""
路由配置与工具函数：
- 通过简单的规则指定哪些命令走 REGEX 或 LLM
- 未命中规则的命令均走 PLY
- 支持复合命令键（如 "OBSERVE FIELD"、"PORT INLET"）
"""
import os
import sys
import re
from typing import Literal

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

class RouteConfig:
    """路由配置类，定义哪些命令使用哪种解析器"""
    
    def __init__(self):
        # 哪些命令可能是"复合前缀"（两词命令名）
        self.MULTIWORD_PREFIXES = {"OBSERVE"}
        
        # REGEX解析器处理的命令（简单、结构化的命令）
        self.REGEX_COMMANDS = {
            # 几何定义类
            "INDUCTOR",
            #"FREESPACE",
            # 可以根据需要添加更多
        }
        
        # LLM解析器处理的命令（复杂、开放式的命令）
        self.LLM_COMMANDS = {
            #"ASSIGN",
            # 函数定义
            #"FUNCTION",
            # 预设命令
            #"PRESET",
            # 发射相关命令
            # "EMISSION", "EMIT",
            # 观测命令
            #"OBSERVE", "OBSERVE FIELD", "OBSERVE FIELD_POWER", "OBSERVE FIELD_INTEGRAL",
            # 端口命令
            #"PORT",
            # 材料定义
            #"CONDUCTOR", 
        }
        
        # LLM解析器处理的前缀（所有以这些词开头的命令）
        self.LLM_PREFIXES = {
            #"OBSERVE",  # 所有OBSERVE开头的命令
        }
        
        # LLM解析器处理的正则模式（包含特定模式的命令）
        self.LLM_PATTERNS = [
            #r".*COMPLEX.*",  # 包含复杂表达式的命令
            #r".*\$.*",       # 包含变量引用的命令
        ]
        
        # 编译正则表达式
        self._compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.LLM_PATTERNS]
    
    def extract_command_key(self, command: str, text: str) -> str:
        """
        生成路由用的键：
        - 若命令在 MULTIWORD_PREFIXES，尝试取 text 的前两个 token 联合作为 key（如 "OBSERVE FIELD"）
        - 否则用单词命令（如 "LINE"、"AREA"）
        """
        tokens = text.split()
        if tokens and tokens[0].upper() in self.MULTIWORD_PREFIXES and len(tokens) >= 2:
            # 第二词只保留字母/下划线，避免括号、符号干扰
            head2 = re.sub(r"[^A-Z_]+", "", tokens[1].upper())
            if head2:
                return f"{tokens[0].upper()} {head2}"
        return command.upper()
    
    def pick_route(self, command: str, text: str) -> Literal["PLY", "REGEX", "LLM"]:
        """
        根据命令和文本内容决定使用哪种解析器
        Args:
            command: 命令名称
            text: 完整的命令文本
        Returns:
            "PLY", "REGEX", 或 "LLM"
        """
        key = self.extract_command_key(command, text)
        
        # 1. 检查是否匹配REGEX规则
        if key in self.REGEX_COMMANDS:
            return "REGEX"
        
        # 2. 检查是否匹配LLM规则
        # 2.1 精确匹配
        if key in self.LLM_COMMANDS:
            return "LLM"
        
        # 2.2 前缀匹配
        for prefix in self.LLM_PREFIXES:
            if key.startswith(prefix):
                return "LLM"
        
        # 2.3 正则模式匹配
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                return "LLM"
        
        # 3. 默认使用PLY解析器
        return "PLY"


# 创建全局路由配置实例
Route_cfg = RouteConfig()