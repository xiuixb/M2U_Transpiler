#######################
# core\muti_flows\mcl_allparser.py
#######################

"""
MCLParser
---------
在路由(route)与转换(conv)之间的“解析调度器”。只负责：
- 输入：route 阶段的分组结果 grouped = {"PLY":[...], "REGEX":[...], "LLM":[...]}
- 处理：
    * PLY 组：一次性批量解析（批量字符串 + 换行填充以对齐过滤后行号）
    * REGEX/LLM 组：逐条解析（通过注入的解析器）
- 输出：按 lineno 升序的一维列表，每条=一行命令的解析结果
    {"lineno", "command", "parser", "ok", "payload", "errors", "text"}

本模块不做文件读写、不打印控制台，便于在 pipeline 中复用。

统一返回对象(内部用 ParseResult)
"""

from __future__ import annotations
import os
import sys

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not (os.path.exists(os.path.join(current_dir, "requirements.txt")) and os.path.isdir(os.path.join(current_dir, "src"))):
    current_dir = os.path.dirname(current_dir)
project_root = current_dir
sys.path.append(project_root)

from typing import Any, Dict, List
from pint import UnitRegistry

from core.muti_flows.mclparser.mcl_plyparser import PLYParser
from core.muti_flows.mclparser.mcl_regex_parser import RegexParser
from core.muti_flows.mclparser.mcl_llmee import LLMParser
from core.muti_flows.mclparser.parser_route import ParserRoute
from core.muti_flows.mclparser.mcl_ast_visit import ASTVisitor
from core.single_flows.mcl_ast import *
from core.symbolBase import ParseResult

# 初始化单位注册表
ureg = UnitRegistry()
default_units = 1 * ureg.meter

# =============================================================================
# 主类
# =============================================================================

class MCLAllParser:
    """
      用法（在 pipeline 中）：
        grouped = {
            "PLY":   [{"lineno":1,"command":"LINE","text":"..."}, ...],
            "REGEX": [{"lineno":2,"command":"AREA","text":"..."}, ...],
            "LLM":   [{"lineno":3,"command":"EMISSION","text":"..."}, ...],
        }
        mp = MCLParser(regex_parser=my_regex, llm_parser=my_llm)
        seq_results = mp.run(grouped)

      属性字段：
        lineno     : 过滤后行号（预处理/路由决定）
        command     : 命令关键字（如 "LINE"/"AREA"/"EMISSION"...）
        payload     : 语义结果（供转换器使用），建议沿用 SymbolTable 的字段组织
        parser_kind : 解析器名（"PLY"|"REGEX"|"LLM" 或自定义）
        ok          : 是否成功解析出语义结果
        errors      : 错误/告警信息列表
        text        : 原始单行命令文本（规范化后的）
    """
    _ply = PLYParser()   # PLY 解析器
    _visitor = ASTVisitor()
    _regex = RegexParser()   # 正则规则解析器
    _llm = LLMParser()     # 大模型推理解析器
    
    def __init__(self, 
                 parser_route: ParserRoute
                 ):
        self.parser_route = parser_route
        

    # ---------------------------- 生命周期 ----------------------------
    def parse_ply_group(self, items: List[dict], line_index) -> List[ParseResult]:
        """
        使用 PLY 解析器批量处理 PLY 组命令。
        """
        ply_ast = self._ply.parse_ply_batch(items=items)
        ply_results = self._visitor.build_sequence(ply_ast, parser_name="PLY", line_index=line_index)
        return ply_results  

    # ---------------------------- REGEX ----------------------------
    def parse_regex_group(self, items: List[dict]) -> List[ParseResult]:
        """
        使用正则解析器逐条处理 REGEX 组命令。
        """
        out: List[ParseResult] = []
        which = "REGEX"
        parser_obj = self._regex

        for it in items:
            text = it.get("text", "").strip()
            if not text:
                continue  # 跳过空行
            lineno = int(it.get("lineno", 0))
            command = it.get("command", "").strip() or "UNKNOWN"

            # ✅ 命令名判空保护
            if not command or command == "UNKNOWN":
                out.append(ParseResult(
                    lineno=lineno,
                    command=command,
                    payload={},
                    parser_kind=which,
                    ok=False, 
                    errors=["missing_or_unknown_command"],
                    text=text
                ))
                continue

            if parser_obj is None:
                out.append(ParseResult(
                    lineno=lineno,
                    command=command,
                    payload={},
                    parser_kind=which,
                    ok=False, 
                    errors=["regex_parser_not_provided"],
                    text=text
                ))
                continue

            try:
                r = parser_obj.parse(command, text, lineno)
                if r is None:
                    out.append(ParseResult(
                        lineno=lineno,
                        command=command,
                        payload={},
                        parser_kind=which,
                        ok=False, 
                        errors=["parser_return_None"],
                        text=text
                    ))

            except Exception as e:
                out.append(ParseResult(
                    lineno=lineno,
                    command=command,
                    payload={},
                    parser_kind=which,
                    ok=False, 
                    errors=[str(e)],
                    text=text
                ))
        return out


    # ---------------------------- LLM ----------------------------
    def parse_llm_group(self, items: List[dict]):
        pass

    # ---------------------------- 总流程 ----------------------------
    def mclparser_in_memory(self, pre_items: list[dict]) -> list[dict]:
        """
        返回统一结构 [{"lineno","command","payload","parser_kind","ok","errors","text"}]
        """
        grouped = self.parser_route.route_items(pre_items)
        print(f"[parser] routing -> { {k: len(v) for k, v in grouped.items()} }")

        line_index = self.build_line_index(grouped)
        ply_results = self.parse_ply_group(grouped.get("PLY", []), line_index)
        
        regex_results = self.parse_regex_group(grouped.get("REGEX", []))

        parsed_result = sorted(ply_results + regex_results, key=lambda r: r.lineno)
        parsed_dict = [self.to_public_dict(r) for r in parsed_result]

        return parsed_dict


    # ---------------------------- 辅助函数 ----------------------------
    @staticmethod
    def to_public_dict(r: ParseResult) -> Dict[str, Any]:
        """ParseResult -> dict
            class ParseResult:
            解析器统一返回的内部对象（仅在内存流转；最终会被转换为对外 dict）。
            属性字段：
            lineno     : 过滤后行号（预处理/路由决定）
            command     : 命令关键字（如 "LINE"/"AREA"/"EMISSION"...）
            payload     : 语义结果（供转换器使用），建议沿用 SymbolTable 的字段组织
            parser_kind : 解析器名（"PLY"|"REGEX"|"LLM" 或自定义）
            ok          : 是否成功解析出语义结果
            errors      : 错误/告警信息列表
            text        : 原始单行命令文本（规范化后的）
        """
        return {
            "lineno": r.lineno,
            "command": r.command,
            "payload": r.payload,
            "parser_kind": r.parser_kind,
            "ok": r.ok,
            "errors": r.errors,
            "text": r.text,
        }
    
    @staticmethod
    def build_line_index(grouped: Dict[str, List[dict]]) -> Dict[int, Dict[str, str]]:
        """
        构建轻量行号索引：
        { lineno: {"command": ..., "text": ...}, ... }

        用于 ASTVisitor.build_sequence() 绑定命令文本信息。
        """
        index: Dict[int, Dict[str, str]] = {}
        for grp_name in ("PLY", "REGEX", "LLM"):
            for item in grouped.get(grp_name, []):
                try:
                    ln = int(item.get("lineno", 0))
                    if ln <= 0:
                        continue
                    index[ln] = {
                        "command": item.get("command", ""),
                        "text": item.get("text", "")
                    }
                except Exception:
                    continue
        return index


