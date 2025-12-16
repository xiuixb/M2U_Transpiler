
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
from pint import UnitRegistry

from src.core_symbol.single_flows.mcl_ast import *
from src.core_symbol.single_flows.mcl_grammar import ply_parser
from src.core_symbol.single_flows.mcl_lexer import lexer
from src.core_symbol.symbolBase import ParseResult

class PLYParser:
    
    # ---------------------------- PLY 批量解析 --------------------------
    @classmethod
    def parse_ply_batch(cls, items: List[dict]) -> ProgramNode:
        """构造带行号对齐的输入源并解析为 AST"""
        if not items:
            return ProgramNode([])

        source = cls._build_padded_source(items)
        lexer.lineno = 1
        ast = ply_parser.parse(source, lexer=lexer, tracking=True)
        return ast


    # ---------------------------- 生成源文本 ----------------------------
    @classmethod
    def _build_padded_source(cls, items: List[dict]) -> str:
        """根据行号拼接带填充换行的完整源文本"""
        chunks: List[str] = []
        curr = 1
        for it in items:
            tgt = int(it["lineno"])
            pad = max(0, tgt - curr)
            if pad:
                chunks.append("\n" * pad)
            t = it["text"]
            chunks.append(t)
            if not t.endswith("\n"):
                chunks.append("\n")
            curr = tgt + 1
        return "".join(chunks)