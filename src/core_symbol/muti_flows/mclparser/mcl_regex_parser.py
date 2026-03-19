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

import re
from typing import Dict, Any, List, Optional
from src.core_symbol.symbolBase import ParseResult

 
class RegexParser:
    """
    自动分发式 REGEX 解析器
    ----------------------------------------
    - 根据命令名自动调用对应 _parse_<command>() 方法
    - 若未定义对应函数，则返回 UNSUPPORTED
    """

    name = "REGEX_PARSER"

    # ===========================================================
    # 主入口
    # ===========================================================
    def parse(self, command: str, text: str, lineno: int) -> Optional[ParseResult]:
        """主入口：自动识别命令并分派"""

        # --- 🟡 判空逻辑：无文本则返回 None ---
        if not text or not text.strip():
            return None  # ✅ 返回 None，不影响结果汇总

        text = text.strip()

        cmd = command
        if not cmd:
            return None

        # 将空格转成下划线，例如 "OBSERVE FIELD" → "_parse_observe_field"
        method_name = f"_parse_{cmd.replace(' ', '_').lower()}"
        handler = getattr(self, method_name, None)

        if handler is None:
            return ParseResult(
                        lineno=lineno,
                        command=command,
                        payload={},
                        parser_kind=self.name,
                        ok=False,
                        errors=f"No handler found for command '{command}'",
                        text=text,
                    )
       
        # 核心代码
        # ======================
        try:
            payload = handler(text)
            return ParseResult(
                        lineno=lineno,
                        command=command,
                        payload=payload,
                        parser_kind=self.name,
                        ok=True,
                        errors="no",
                        text=text
                    )
        # ======================

        except Exception as e:
            return ParseResult(
                        lineno=lineno,
                        command=command,
                        payload={},
                        parser_kind=self.name,
                        ok=False,
                        errors=str(e),
                        text=text
                    )

    # ===========================================================
    # 各命令解析函数
    # ===========================================================

    def _parse_outgoing(self, text: str) -> Dict[str, Any]:
        """OUTGOING geom_name direction (TE|TM|ALL);"""
        m = re.match(r"OUTGOING\s+(\w+)\s+(POSITIVE|NEGATIVE)\s+(TE|TM|ALL)\s*;?", text, re.IGNORECASE)
        if not m:
            raise ValueError("OUTGOING syntax invalid")
        geom, direction, mode = m.groups()
        return {
            "kind": "OUTGOING",
            "geom_name": geom,
            "direction": direction.upper(),
            "mode": mode.upper()
        }
    
    def _parse_inductor(self, text: str) -> Dict[str, Any]:
        """
        INDUCTOR命令解析（关键字分段法）
        
        分段关键字：
          INDUCTOR, INDUCTANCE, MATERIAL, RESISTIVITY, RESISTANCE, NUMBER
        """
        # ========== 预处理 ==========
        clean_text = text.replace(";", "").strip()
        tokens = clean_text.split()
        result: Dict[str, Any] = {"kind": "INDUCTOR"}

        # 所有可能关键字
        keywords = ["INDUCTOR", "INDUCTANCE", "MATERIAL", "RESISTIVITY", "RESISTANCE", "NUMBER"]

        # 找出关键字起始索引
        indices = []
        for i, tok in enumerate(tokens):
            if tok.upper() in keywords:
                indices.append((tok.upper(), i))
        indices.append(("END", len(tokens)))  # 方便切片

        # ========== 分段提取 ==========
        for j in range(len(indices) - 1):
            key, start = indices[j]
            _, end = indices[j + 1]
            segment = tokens[start:end]

            # -------------------- 段1: INDUCTOR --------------------
            if key == "INDUCTOR":
                # 格式: INDUCTOR <line_name> <diameter(...)>
                if len(segment) >= 2:
                    result["line_name"] = segment[1]
                if len(segment) > 2:
                    # 剩下的所有内容即为直径表达式
                    result["diameter"] = " ".join(segment[2:]).strip()

            # -------------------- 段2: INDUCTANCE --------------------
            elif key == "INDUCTANCE" and len(segment) >= 2:
                result["inductance"] = segment[1]

            # -------------------- 段3: MATERIAL --------------------
            elif key == "MATERIAL":
                # 格式: MATERIAL name frequency
                if len(segment) >= 3:
                    result["material"] = {
                        "name": segment[1],
                        "frequency": segment[2]
                    }

            # -------------------- 段4: RESISTIVITY --------------------
            elif key == "RESISTIVITY" and len(segment) >= 2:
                result["resistivity"] = segment[1]

            # -------------------- 段5: RESISTANCE --------------------
            elif key == "RESISTANCE" and len(segment) >= 2:
                result["resistance"] = segment[1]

            # -------------------- 段6: NUMBER --------------------
            elif key == "NUMBER" and len(segment) >= 2:
                result["number"] = segment[1]

        return result

    def _parse_freespace(self, text: str) -> Dict[str, Any]:
        """
        FREESPACE命令解析（关键字分段法）
        -------------------------------------------------------
        语法:
            FREESPACE {area|volume} {POSITIVE|NEGATIVE} {X1|X2|X3}
                      {TRANSVERSE|ALL|E1|E2|B3}
                [CONDUCTIVITY f(x)]
                [ELECTRIC_CONDUCTIVITY fE(x)]
                [MAGNETIC_CONDUCTIVITY fB(x)]
                [{TERMINATE_WITH_SHORT | NO_TERMINATE_WITH_SHORT}] ;
        """
        # ========== 预处理 ==========
        clean_text = text.replace(";", "").replace(",", " ").strip()
        tokens = clean_text.split()
        result: Dict[str, Any] = {"kind": "FREESPACE"}

        # 定义关键字
        keywords = [
            "FREESPACE", "CONDUCTIVITY", "ELECTRIC_CONDUCTIVITY",
            "MAGNETIC_CONDUCTIVITY", "TERMINATE_WITH_SHORT", "NO_TERMINATE_WITH_SHORT"
        ]

        # 找出关键字索引
        indices = []
        for i, tok in enumerate(tokens):
            if tok.upper() in keywords:
                indices.append((tok.upper(), i))
        indices.append(("END", len(tokens)))  # 方便切片

        # ========== 分段提取 ==========
        for j in range(len(indices) - 1):
            key, start = indices[j]
            _, end = indices[j + 1]
            segment = tokens[start:end]

            # -------------------- 段1: FREESPACE --------------------
            if key == "FREESPACE":
                # 格式: FREESPACE geom_name direction axis mode
                # 如: FREESPACE OUTAREA NEGATIVE X1 ALL
                try:
                    result["geom_name"] = segment[1] if len(segment) > 1 else ""
                    result["direction"] = segment[2].upper() if len(segment) > 2 else ""
                    result["axis"] = segment[3].upper() if len(segment) > 3 else ""
                    result["mode"] = segment[4].upper() if len(segment) > 4 else ""
                except Exception:
                    raise ValueError(f"Invalid FREESPACE syntax: {text}")

            # -------------------- 段2: CONDUCTIVITY --------------------
            elif key == "CONDUCTIVITY" and len(segment) >= 2:
                result["conductivity"] = " ".join(segment[1:]).strip()

            # -------------------- 段3: ELECTRIC_CONDUCTIVITY --------------------
            elif key == "ELECTRIC_CONDUCTIVITY" and len(segment) >= 2:
                result["electric_conductivity"] = " ".join(segment[1:]).strip()

            # -------------------- 段4: MAGNETIC_CONDUCTIVITY --------------------
            elif key == "MAGNETIC_CONDUCTIVITY" and len(segment) >= 2:
                result["magnetic_conductivity"] = " ".join(segment[1:]).strip()

            # -------------------- 段5: TERMINATE_WITH_SHORT --------------------
            elif key == "TERMINATE_WITH_SHORT":
                result["terminate_with_short"] = True

            # -------------------- 段6: NO_TERMINATE_WITH_SHORT --------------------
            elif key == "NO_TERMINATE_WITH_SHORT":
                result["terminate_with_short"] = False

        return result

    


