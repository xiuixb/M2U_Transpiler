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

from src.domain.mclparse.mcl_plyparser import PLYParser
from src.domain.mclparse.mcl_regex_parser import RegexParser
from src.domain.mclparse.mcl_llmparser import LLMParser
from src.domain.mclparse.parser_classifier import ParserClassifier
from src.domain.mclparse.mcl_ast_visit import ASTVisitor
from src.domain.mclparse.plyparser.mcl_ast import *
from src.domain.config.symbolBase import ParseResult
from src.domain.core.llm_flows import MCLPromptBuildFlow
from src.infrastructure.llm_config import llm_config


# 初始化单位注册表
ureg = UnitRegistry()
default_units = 1 * ureg.meter

# =============================================================================
# 主类
# =============================================================================

class MCLParseFlow:
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
    _llm = None     # 大模型推理解析器（延迟初始化）
    
    def __init__(self, 
                 parser_classifier: ParserClassifier
                 ):
        self.parser_classifier = parser_classifier
        

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
                            errors="ply_no_statement",
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
                            errors="visitor_no_result",
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
                        errors=f"ply_error: {e}",
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
                        errors="missing_or_unknown_command",
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
                        errors="regex_parser_not_provided",
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
                            errors="parser_return_None",
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
                        errors=str(e),
                        text=text,
                    )
                )
        return out


    # ---------------------------- LLM ----------------------------
    def parse_llm_group(self, items: List[dict]) -> List[ParseResult]:
        """
        使用LLM解析器批量处理 LLM 组命令。
        实现真正的全并发：所有批次（不管什么命令类型）全部并行处理。
        """
        import time
        
        out: List[ParseResult] = []
        which = "LLM"
        
        if not items:
            return out
        
        # 记录LLM解析开始时间
        llm_start_time = time.time()
        print(f"[info] LLM解析: 开始时间 {time.strftime('%H:%M:%S', time.localtime(llm_start_time))}")
        
        # 延迟初始化LLM解析器
        if self._llm is None:
            try:
                self._llm = LLMParser()
                self.prompt_flow = MCLPromptBuildFlow()
                self._llm.load_entity(
                    api_key=llm_config.api_key,
                    prompt_flow=self.prompt_flow
                )
                print("[info] LLM解析器初始化成功")
            
            except Exception as e:
                print(f"[ERROR] LLM解析器初始化失败: {e}")
                # 返回所有项目的失败结果
                for item in items:
                    out.append(
                        ParseResult(
                            lineno=int(item.get("lineno", 0)),
                            command=item.get("command", ""),
                            payload={},
                            parser_kind=which,
                            ok=False,
                            errors=f"llm_init_failed: {e}",
                            text=item.get("text", ""),
                        )
                    )
                return out
        
        # 按命令类型分组 - defaultdict会自动为新键创建空列表
        command_groups = defaultdict(list)
        for item in items:
            command = item.get("command", "").upper()
            command_groups[command].append(item)
        
        print(f"[info] LLM解析: 开始批量解析 {len(items)} 条命令，分为 {len(command_groups)} 个命令类型")
        
        # 初始化统计变量
        total_success = 0
        total_failed = 0
        
        # 使用全并发策略处理所有命令类型和批次
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # 过滤掉空的命令组
        valid_command_groups = {cmd_type: cmd_items for cmd_type, cmd_items in command_groups.items() if cmd_items}
        
        if not valid_command_groups:
            print("[info] LLM解析: 没有有效的命令需要处理")
            return out
        
        # 🚀 关键优化：创建所有批次任务列表，实现真正的全并发
        all_batch_tasks = []
        total_batches_count = 0
        
        for command_type, cmd_items in valid_command_groups.items():
            print(f"[info] LLM解析: 准备 {command_type} 命令，共 {len(cmd_items)} 条")
            
            # 将命令分批 - 使用4条命令的批次大小，平衡效率和响应时间
            batch_size = 4  # 4条命令的批次大小，在效率和时间间找到平衡
            batches = []
            for i in range(0, len(cmd_items), batch_size):
                batch = cmd_items[i:i + batch_size]
                batches.append(batch)
            
            # 为每个批次创建任务
            for batch_index, batch in enumerate(batches):
                task_info = {
                    'command_type': command_type,
                    'batch': batch, 
                    'batch_index': batch_index, 
                    'total_batches_for_command': len(batches),
                    'global_batch_id': total_batches_count  # 全局批次ID
                }
                all_batch_tasks.append(task_info)
                total_batches_count += 1
        
        print(f"[info] LLM解析: 🚀 总共创建 {len(all_batch_tasks)} 个批次任务，准备全并发处理")
        print(f"[info] LLM解析: 💡 优化效果：所有批次将同时并行，不再受命令类型限制")
        
        # 🚀 使用更大的线程池，实现真正的全并发
        # 激进配置：使用12个并发批次，充分利用API性能
        max_concurrent_batches = min(12, len(all_batch_tasks))  # 激进配置：最多12个批次同时处理
        
        with ThreadPoolExecutor(max_workers=max_concurrent_batches) as executor:
            # 提交所有批次任务
            future_to_task = {}
            for task_info in all_batch_tasks:
                future = executor.submit(self._process_single_batch, task_info, which)
                future_to_task[future] = task_info
            
            print(f"[info] LLM解析: 已提交 {len(future_to_task)} 个批次任务到 {max_concurrent_batches} 个并发线程")
            
            # 收集所有批次的处理结果
            completed_count = 0
            for future in as_completed(future_to_task):
                task_info = future_to_task[future]
                command_type = task_info['command_type']
                batch_index = task_info['batch_index']
                global_batch_id = task_info['global_batch_id']
                
                # 记录批次完成时间
                batch_end_time = time.time()
                batch_end_timestamp = time.strftime('%H:%M:%S', time.localtime(batch_end_time))
                
                try:
                    batch_results, batch_success, batch_failed = future.result()
                    out.extend(batch_results)
                    total_success += batch_success
                    total_failed += batch_failed
                    
                    completed_count += 1
                    batch_duration = batch_end_time - llm_start_time
                    print(f"[info] LLM解析: ✅ [{batch_end_timestamp}] {command_type} 批次 {batch_index + 1} 完成 (全局批次 {global_batch_id + 1}, 进度 {completed_count}/{len(all_batch_tasks)}, 耗时 {batch_duration:.1f}s)")
                    
                except Exception as e:
                    print(f"[ERROR] LLM解析: ❌ [{batch_end_timestamp}] {command_type} 批次 {batch_index + 1} 时出错: {e}")
                    # 为该批次的所有项目返回失败结果
                    batch = task_info['batch']
                    for item in batch:
                        out.append(
                            ParseResult(
                                lineno=int(item.get("lineno", 0)),
                                command=command_type,
                                payload={},
                                parser_kind=which,
                                ok=False,
                                errors=f"batch_concurrent_exception: {str(e)}",
                                text=item.get("text", ""),
                            )
                        )
                        total_failed += 1
        
        print(f"[info] LLM解析: 🎉 批量解析完成，成功 {total_success} 条，失败 {total_failed} 条")
        
        # 记录LLM解析结束时间
        llm_end_time = time.time()
        llm_duration = llm_end_time - llm_start_time
        print(f"[info] LLM解析: 结束时间 {time.strftime('%H:%M:%S', time.localtime(llm_end_time))}")
        print(f"[info] LLM解析: ⚡ 总耗时 {llm_duration:.2f}秒 (全并发优化)")
        
        # 按行号排序返回结果
        out.sort(key=lambda r: r.lineno)
        return out

    def _process_single_batch(self, task_info: dict, which: str):
        """处理单个批次的命令
        
        Args:
            task_info: 包含批次信息的字典
            which: 解析器类型标识
            
        Returns:
            tuple: (results_list, success_count, failed_count)
        """
        import time
        
        command_type = task_info['command_type']
        batch = task_info['batch']
        batch_index = task_info['batch_index']
        global_batch_id = task_info['global_batch_id']
        
        # 记录批次开始时间
        batch_start_time = time.time()
        batch_start_timestamp = time.strftime('%H:%M:%S', time.localtime(batch_start_time))
        
        results = []
        success_count = 0
        failed_count = 0
        
        try:
            print(f"[info] LLM解析: 🚀 [{batch_start_timestamp}] 开始处理 {command_type} 批次 {batch_index + 1} (全局批次 {global_batch_id + 1})，共 {len(batch)} 条命令")
            
            # 直接调用LLM解析器处理这个批次
            model_name = "qwen-plus"
            
            # 调用LLM解析器的单批次处理方法
            llm_results = self._llm._parse_batch_with_json_retry(model_name, command_type, batch, batch_index)
            
            # 记录LLM调用完成时间
            llm_end_time = time.time()
            llm_duration = llm_end_time - batch_start_time
            llm_end_timestamp = time.strftime('%H:%M:%S', time.localtime(llm_end_time))
            
            # 处理LLM返回的结构化结果
            if llm_results and isinstance(llm_results, list):
                print(f"[info] LLM解析: 📝 [{llm_end_timestamp}] {command_type} 批次 {batch_index + 1} LLM调用完成，耗时 {llm_duration:.1f}s，开始后处理")
                
                # 处理每个LLM解析结果
                for llm_result in llm_results:
                    if not isinstance(llm_result, dict):
                        continue
                        
                    # 从LLM结果中提取信息
                    result_lineno = int(llm_result.get("lineno", 0))
                    
                    # 检查LLM解析是否成功（LLM后处理已经设置了ok字段）
                    llm_success = llm_result.get("ok", False)
                    llm_payload = llm_result.get("payload", {})
                    llm_errors = llm_result.get("errors", "no")
                    llm_text = llm_result.get("text", "")
                    
                    # 统一errors字段为字符串类型
                    if isinstance(llm_errors, list):
                        if not llm_errors or (len(llm_errors) == 1 and llm_errors[0] == "no"):
                            llm_errors = "no"
                        else:
                            llm_errors = "; ".join(str(e) for e in llm_errors)
                    elif llm_errors is None:
                        llm_errors = "no"
                    else:
                        llm_errors = str(llm_errors)
                    
                    if llm_success and llm_payload:
                        # 解析成功
                        results.append(
                            ParseResult(
                                lineno=result_lineno,
                                command=command_type,
                                payload=llm_payload,
                                parser_kind=which,
                                ok=True,
                                errors="no",
                                text=llm_text,
                            )
                        )
                        success_count += 1
                    else:
                        # 解析失败
                        results.append(
                            ParseResult(
                                lineno=result_lineno,
                                command=command_type,
                                payload={},
                                parser_kind=which,
                                ok=False,
                                errors=llm_errors if llm_errors != "no" else "llm_parse_failed",
                                text=llm_text,
                            )
                        )
                        failed_count += 1
                
                # 检查是否有项目没有得到处理结果
                processed_linenos = {int(r.get("lineno", 0)) for r in llm_results}
                for item in batch:
                    item_lineno = int(item.get("lineno", 0))
                    if item_lineno not in processed_linenos:
                        results.append(
                            ParseResult(
                                lineno=item_lineno,
                                command=command_type,
                                payload={},
                                parser_kind=which,
                                ok=False,
                                errors="llm_no_result",
                                text=item.get("text", ""),
                            )
                        )
                        failed_count += 1
                        
                # 记录批次完成时间
                batch_end_time = time.time()
                total_duration = batch_end_time - batch_start_time
                batch_end_timestamp = time.strftime('%H:%M:%S', time.localtime(batch_end_time))
                print(f"[info] LLM解析: ✅ [{batch_end_timestamp}] {command_type} 批次 {batch_index + 1} 处理完成，总耗时 {total_duration:.1f}s，成功 {success_count}，失败 {failed_count}")
                
            else:
                # LLM返回空结果或格式错误
                llm_end_timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
                print(f"[WARNING] [{llm_end_timestamp}] {command_type} 批次 {batch_index + 1} 的LLM解析返回空结果")
                for item in batch:
                    results.append(
                        ParseResult(
                            lineno=int(item.get("lineno", 0)),
                            command=command_type,
                            payload={},
                            parser_kind=which,
                            ok=False,
                            errors="llm_empty_result",
                            text=item.get("text", ""),
                        )
                    )
                    failed_count += 1
                    
        except Exception as e:
            error_timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
            print(f"[ERROR] [{error_timestamp}] LLM解析 {command_type} 批次 {batch_index + 1} 时出错: {e}")
            # 为该批次的所有项目返回失败结果
            for item in batch:
                results.append(
                    ParseResult(
                        lineno=int(item.get("lineno", 0)),
                        command=command_type,
                        payload={},
                        parser_kind=which,
                        ok=False,
                        errors=f"batch_exception: {str(e)}",
                        text=item.get("text", ""),
                    )
                )
                failed_count += 1
        
        return results, success_count, failed_count


    # ---------------------------- 总流程 ----------------------------
    def mclparser_in_memory(self, pre_items: list[dict]) -> list[dict]:
        """
        输入预处理后的
        返回统一结构 [{"lineno","command","payload","parser_kind","ok","errors","text"}]
        """

        grouped = self.parser_classifier.classify_items(pre_items)
        print(f"[parser] routing -> { {k: len(v) for k, v in grouped.items()} }")

        # PLY 组逐条解析
        ply_results = self.parse_ply_group(grouped.get("PLY", []))

        # REGEX 组逐条解析
        regex_results = self.parse_regex_group(grouped.get("REGEX", []))

        # LLM 组逐条解析
        llm_results = self.parse_llm_group(grouped.get("LLM", []))

        all_results: List[ParseResult] = sorted(
            ply_results + regex_results + llm_results,
            key=lambda r: r.lineno,
        )

        # ---------------- 解析结果汇总统计 ----------------
        total = len(all_results)
        ok_cnt = sum(1 for r in all_results if r.errors == "no")
        fail_cnt = total - ok_cnt

        by_kind = defaultdict(lambda: {"ok": 0, "fail": 0})
        failed_items: List[ParseResult] = []

        for r in all_results:
            if r.errors == "no":
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
                    f"cmd={r.command}, errors={r.errors[:120]}"
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
            "ok": r.errors == "no",
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


