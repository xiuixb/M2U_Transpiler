"""
路由配置与工具函数：
- 通过 EXACT / PREFIX / REGEX 三类规则指定哪些命令走 REGEX 或 LLM
- 未命中规则的命令均走 PLY
- 支持抽取复合命令键（如 "OBSERVE FIELD"、"PORT INLET"），优先两词，再回退到第一词
"""
# from __future__ import annotations
import os
import sys

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from src.core_symbol.rules import RuleBucket, RouteRule

# 哪些命令可能是“复合前缀”（两词命令名）
MULTIWORD_PREFIXES = {"OBSERVE", "PORT"}  # 按需扩展

# ==== 在这里编辑你的规则 ====
# 示例：正则解析器优先处理几何/简单格式命令；LLM 兜底处理开放式/弱结构命令
REGEX_RULES = RuleBucket.from_patterns(
    exact=[                                   # 键匹配
        "INDUCTOR",
        "FREESPACE"
    ],
    prefix=[
        #"OBSERVE FIELD"                       # 前缀匹配
    ],
    regex=[
        #r"^LINE\b.*CONFORMAL\b",             # 文本正则匹配
    ],
)

LLM_RULES = RuleBucket.from_patterns(
    exact=[
        #"EMISSION", "EMIT"        # 若你打算让发射语句临时走 LLM 兜底
    ],
    prefix=[
        # "MATERIAL",              # 例如：想让所有 MATERIAL* 走 LLM 就打开
    ],
    regex=[
        #r"\bFREE\s*TEXT\b",        
    ],
)

Route_cfg = RouteRule(regex_rules=REGEX_RULES, llm_rules=LLM_RULES, MULTIWORD_PREFIXES=MULTIWORD_PREFIXES)
