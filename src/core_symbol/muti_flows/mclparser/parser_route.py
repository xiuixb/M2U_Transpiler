################################
# core\muti_flows\mclparser\parser_route.py
################################
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

from pathlib import Path
import json
from typing import Dict, List

from src.core_symbol.rules import RouteRule

class ParserRoute:
    def __init__(self, config: RouteRule):
        self.config = config
        
    # --------------- 纯函数：内存 -> 内存 ---------------
    def route_items(self, items: List[dict]) -> Dict[str, List[dict]]:
        """
        输入: items = [{"lineno":..., "command":..., "text":...}, ...]
        输出: {"PLY":[...], "REGEX":[...], "LLM":[...]}
        """
        out = {"PLY": [], "REGEX": [], "LLM": []}
        for obj in items:
            command = (obj.get("command") or "").strip().upper()
            text = obj.get("text") or ""
            route = self.config.pick_route(command, text)  # "PLY" / "REGEX" / "LLM"
            out[route].append(obj)
        return out

    # --------------- 文件封装：jsonl -> 单一 json ---------------
    def derive_output_path(self, jsonl_file: str, *, suffix: str = "_routed.json") -> Path:
        p = Path(jsonl_file)
        return p.parent / f"{p.stem}{suffix}"

    def route_jsonl_file(self, jsonl_file: str, *, outfile: str | None = None) -> Dict[str, List[dict]]:
        """
        读取 jsonl -> 分流 -> 写入一个 JSON 文件（包含三组）
        返回分流后的 dict（同 route_items）
        """
        jsonl_path = Path(jsonl_file)
        items: List[dict] = []
        with open(jsonl_path, "r", encoding="utf-8") as fj:
            for line in fj:
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))

        grouped = self.route_items(items)

        out_path = Path(outfile) if outfile else self.derive_output_path(str(jsonl_path))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(grouped, f, ensure_ascii=False, indent=2)

        return grouped

