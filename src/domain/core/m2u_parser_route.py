"""
==========================
src/domain/mclparse/m2u_parser_route.py
==========================
定义了MCL2UNIPIC的解析路由配置，包括：
- 多词前缀
- REGEX解析器处理的命令
- LLM解析器处理的命令
- LLM解析器处理的前缀
- LLM解析器处理的正则模式
"""

import re
from typing import Literal


class ParseRouteConfig:
    """路由配置类，定义哪些命令使用哪种解析器"""

    def load_config(self,
                     multiword_prefixes: set,
                     regex_commands: set,                     
                     llm_commands: set,
                     llm_prefixes: set,
                     llm_patterns: list,
                    ):
        """从参数加载路由配置"""
        self.REGEX_COMMANDS = regex_commands
        self.MULTIWORD_PREFIXES = multiword_prefixes
        self.LLM_COMMANDS = llm_commands
        self.LLM_PREFIXES = llm_prefixes
        self.LLM_PATTERNS = llm_patterns
        self._compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.LLM_PATTERNS]
        if False:   
            print(f"MULTIWORD_PREFIXES: {self.MULTIWORD_PREFIXES}\n")
            print(f"REGEX_COMMANDS: {self.REGEX_COMMANDS}\n")
            print(f"LLM_COMMANDS: {self.LLM_COMMANDS}\n")
            print(f"LLM_PREFIXES: {self.LLM_PREFIXES}\n")
            print(f"LLM_PATTERNS: {self.LLM_PATTERNS}\n")
    
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
parse_route_cfg = ParseRouteConfig()