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
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from typing import Any, Dict, List
from collections import defaultdict
from pint import UnitRegistry

from src.core_symbol.muti_flows.mclparser.mcl_plyparser import PLYParser
from src.core_symbol.muti_flows.mclparser.mcl_regex_parser import RegexParser
from src.core_cac.mcl_llmparser import LLMParser
from src.core_symbol.muti_flows.mclparser.parser_route import ParserRoute
from src.core_symbol.muti_flows.mclparser.mcl_ast_visit import ASTVisitor
from src.core_symbol.single_flows.mcl_ast import *
from src.core_symbol.symbolBase import ParseResult

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
        

    # ---------------------------- PLY ----------------------------
    def parse_ply_group(self, items: List[dict]) -> List[ParseResult]:
        """
        使用 PLY 解析器逐条处理 PLY 组命令（逐行解析）。
        每个 item 独立送进 PLY，单条出错不会影响其它行。
        """
        out: List[ParseResult] = []

        if not items:
            return out

        for it in items:
            lineno = int(it.get("lineno", 0))
            command = it.get("command", "").strip() or "UNKNOWN"
            text = it.get("text", "")

            # 单条命令的元信息，用于 ASTVisitor 绑定 command/text
            line_index_single = {
                lineno: {
                    "command": command,
                    "text": text,
                }
            }

            try:
                # 复用现有的批量接口，只传入单个 item
                program = self._ply.parse_ply_batch([it])

                # PLY 语法严重错误时，可能返回 None 或 statements 为空
                if program is None or not getattr(program, "statements", None):
                    out.append(
                        ParseResult(
                            lineno=lineno,
                            command=command,
                            payload={},
                            parser_kind="PLY",
                            ok=False,
                            errors=["ply_no_statement"],
                            text=text,
                        )
                    )
                    continue

                # 通过 ASTVisitor 将 ProgramNode -> ParseResult 列表
                seq = self._visitor.build_sequence(
                    program,
                    parser_name="PLY",
                    line_index=line_index_single,
                )

                # 正常情况下，单条命令应产出 1 个 ParseResult
                if seq:
                    out.extend(seq)
                else:
                    out.append(
                        ParseResult(
                            lineno=lineno,
                            command=command,
                            payload={},
                            parser_kind="PLY",
                            ok=False,
                            errors=["visitor_no_result"],
                            text=text,
                        )
                    )

            except Exception as e:
                # 捕获任意异常，保证这一行错误不会拖死整个解析流程
                out.append(
                    ParseResult(
                        lineno=lineno,
                        command=command,
                        payload={},
                        parser_kind="PLY",
                        ok=False,
                        errors=[f"ply_error: {e}"],
                        text=text,
                    )
                )

        # 最终按 lineno 排序，保证与后续转换的假设一致
        out.sort(key=lambda r: r.lineno)
        return out 

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

            # 命令名判空保护
            if not command or command == "UNKNOWN":
                out.append(
                    ParseResult(
                        lineno=lineno,
                        command=command,
                        payload={},
                        parser_kind=which,
                        ok=False,
                        errors=["missing_or_unknown_command"],
                        text=text,
                    )
                )
                continue

            if parser_obj is None:
                out.append(
                    ParseResult(
                        lineno=lineno,
                        command=command,
                        payload={},
                        parser_kind=which,
                        ok=False,
                        errors=["regex_parser_not_provided"],
                        text=text,
                    )
                )
                continue

            try:
                r = parser_obj.parse(command, text, lineno)
                if r is None:
                    out.append(
                        ParseResult(
                            lineno=lineno,
                            command=command,
                            payload={},
                            parser_kind=which,
                            ok=False,
                            errors=["parser_return_None"],
                            text=text,
                        )
                    )
                else:
                    # ✅ 解析成功的结果要 append 出去
                    out.append(r)

            except Exception as e:
                out.append(
                    ParseResult(
                        lineno=lineno,
                        command=command,
                        payload={},
                        parser_kind=which,
                        ok=False,
                        errors=[str(e)],
                        text=text,
                    )
                )
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

        # PLY 组逐条解析
        ply_results = self.parse_ply_group(grouped.get("PLY", []))

        # REGEX 组逐条解析
        regex_results = self.parse_regex_group(grouped.get("REGEX", []))

        # 未来如果支持 LLM 组，这里再补充 parse_llm_group(...)
        all_results: List[ParseResult] = sorted(
            ply_results + regex_results,
            key=lambda r: r.lineno,
        )

        # ---------------- 解析结果汇总统计 ----------------
        total = len(all_results)
        ok_cnt = sum(1 for r in all_results if r.ok)
        fail_cnt = total - ok_cnt

        by_kind = defaultdict(lambda: {"ok": 0, "fail": 0})
        failed_items: List[ParseResult] = []

        for r in all_results:
            if r.ok:
                by_kind[r.parser_kind]["ok"] += 1
            else:
                by_kind[r.parser_kind]["fail"] += 1
                failed_items.append(r)

        print("\n[parser] ===== Parse summary =====")
        print(f"[parser] total   : {total}")
        print(f"[parser] success : {ok_cnt}")
        print(f"[parser] failed  : {fail_cnt}")

        print("[parser] by parser_kind:")
        for kind, stat in by_kind.items():
            print(f"  - {kind:6s}  ok={stat['ok']:4d}  fail={stat['fail']:4d}")

        if failed_items:
            print("[parser] failed items (lineno, parser, command):")
            for r in failed_items:
                # 只打印行号 + 解析类型 + 命令，错误详情留在 errors 字段里
                print(
                    f"    line={r.lineno:4d}, parser={r.parser_kind:6s}, "
                    f"cmd={r.command}, errors={'; '.join(r.errors)[:120]}"
                )
        else:
            print("[parser] no failed items.")
        print("[parser] =========================\n")

        # ---------------- 组装对外 dict 结果 ----------------
        parsed_dict = [self.to_public_dict(r) for r in all_results]
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


