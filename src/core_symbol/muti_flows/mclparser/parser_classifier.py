################################
# core\muti_flows\mclparser\parser_classifier.py
################################
"""
命令分类器：根据路由配置将命令分类到不同的解析器
- PLY: 传统语法解析器
- REGEX: 正则表达式解析器  
- LLM: 大语言模型解析器
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

import json
from pathlib import Path
from typing import Dict, List
from src.core_symbol.muti_flows.mclparser.m2u_parser_route import ParseRouteConfig

class ParserClassifier:
    """命令分类器，将命令按照路由规则分配给不同的解析器"""
    
    def __init__(self, route_config: ParseRouteConfig):
        self.route_config = route_config
        
    # --------------- 纯函数：内存 -> 内存 ---------------
    def classify_items(self, items: List[dict]) -> Dict[str, List[dict]]:
        """
        将命令项目分类到不同的解析器
        输入: items = [{"lineno":..., "command":..., "text":...}, ...]
        输出:         
        grouped = {
            "PLY":   [{"lineno":..., "command":"...","text":"..."}, ...],
            "REGEX": [{"lineno":..., "command":"...","text":"..."}, ...],
            "LLM":   [{"lineno":..., "command":"...","text":"..."}, ...],
        }
        """
        out = {"PLY": [], "REGEX": [], "LLM": []}
        for obj in items:
            command = (obj.get("command") or "").strip().upper()
            text = obj.get("text") or ""
            parser_type = self.route_config.pick_route(command, text)  # 核心代码："PLY" / "REGEX" / "LLM"
            out[parser_type].append(obj)
        return out

    # 保持向后兼容的别名
    def route_items(self, items: List[dict]) -> Dict[str, List[dict]]:
        """向后兼容的方法名"""
        return self.classify_items(items)

    # --------------- 文件封装：jsonl -> 单一 json ---------------
    def derive_output_path(self, jsonl_file: str, *, suffix: str = "_classified.json") -> Path:
        p = Path(jsonl_file)
        return p.parent / f"{p.stem}{suffix}"

    def classify_jsonl_file(self, jsonl_file: str, *, outfile: str | None = None) -> Dict[str, List[dict]]:
        """
        读取 jsonl -> 分类 -> 写入一个 JSON 文件（包含三组）
        返回分类后的 dict（同 classify_items）
        """
        jsonl_path = Path(jsonl_file)
        items: List[dict] = []
        with open(jsonl_path, "r", encoding="utf-8") as fj:
            for line in fj:
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))

        grouped = self.classify_items(items)

        out_path = Path(outfile) if outfile else self.derive_output_path(str(jsonl_path))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(grouped, f, ensure_ascii=False, indent=2)

        return grouped
