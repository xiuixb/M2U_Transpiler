#######################
# core\muti_flows\mcl_preprocess.py
#######################
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
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from pint import UnitRegistry

ureg = UnitRegistry()

from src.core_symbol.muti_flows.utils.mcl_tokenizer import Tokenizer
from src.core_symbol.muti_flows.utils.cmd_dic import CMD_KEYWORDS_MULTI, CMD_KEYWORDS_SINGLE
from src.core_symbol.rules import PreprocessRules


class M2DPreprocess:
    """
    简化版预处理器：
    - 保留阶段1：注释过滤 + 多行合并
    - 保留阶段2：POINT 展开、命令过滤
    - 去掉阶段3的全部数学解析 / Tokenizer / 单位处理
    """
    def __init__(self, rules: PreprocessRules):
        self.rules = rules

    def replace_all(self, text, from_str, to_str):
        return text.replace(from_str, to_str)

    # ---------- 主流程 ----------
    def mcl_preprocess(self, input_lines: List[str]) -> List[Dict[str, str]]:
        """
        返回格式：
        [
            {"lineno": <顺序号>, "command": <命令名>, "text": <完整命令文本>},
        ]
        """

        # ==========================================================
        # 阶段 1：合并单行命令 (处理 inline_enter、注释过滤)
        # ==========================================================
        buffer = ""
        start_lineno = 0
        collected: List[Tuple[int, str]] = []  # [(orig_lineno, merged_cmd)]

        for i, raw in enumerate(input_lines, start=1):

            if not raw.strip():
                continue
            if raw.strip().startswith(("!", "C ", "Z ")):
                continue

            line = raw.upper()
            stripped = line.split("!")[0].strip()
            if not stripped:
                continue

            # 开始新的命令
            if buffer == "":
                buffer = stripped
                start_lineno = i
            else:
                buffer += " inline_enter " + stripped

            # 命令结束
            if ";" in stripped:
                collected.append((start_lineno, buffer.strip()))
                buffer = ""
                start_lineno = 0

        # ==========================================================
        # 阶段 2：POINT 展开、过滤 commands_to_skip
        # ==========================================================
        point_table: Dict[str, str] = {}
        expanded_cmds: List[Tuple[int, str]] = []

        for lineno, cmd in collected:

            # ---- 格式化一些符号使得 token 位置稳定 ----
            cmd_format = (
                cmd.replace(";", " ; ")
                   .replace(",", " , ")
                   .replace("=", " = ")
            )

            tokens = cmd_format.split()
            if not tokens:
                continue

            first = tokens[0]

            # ---- command 过滤 ----
            if first in self.rules.commands_to_skip:
                continue

            # 过滤 options
            if first in self.rules.commands_to_skip_byOptions:
                skip_opts = self.rules.commands_to_skip_byOptions[first]
                if any(opt in cmd_format for opt in skip_opts):
                    continue

            # 强制删除某些 options
            if first in self.rules.options_to_skip:
                skip_opts = self.rules.options_to_skip[first]
                possible_opts = self.rules.options_of_command.get(first, [])
                new_tokens = []
                i = 0
                while i < len(tokens):
                    tok = tokens[i]
                    if tok in skip_opts:
                        i += 1
                        while (
                            i < len(tokens)
                            and tokens[i] not in possible_opts
                            and tokens[i] != ";"
                        ):
                            i += 1
                    else:
                        new_tokens.append(tok)
                        i += 1
                cmd_format = " ".join(new_tokens)

            # ---- POINT 定义 ----
            toks = cmd_format.split()
            if not toks:
                continue
            first = toks[0]

            if first == "POINT":
                name = toks[1]
                coords = " ".join(toks[2:-1])  # 去掉末尾 ;
                point_table[name] = coords

            # ---- LINE 或 AREA 使用 POINT ---
            if first in ("LINE", "AREA"):
                new_tokens = []
                for tok in toks:
                    if tok in point_table:
                        new_tokens.extend(point_table[tok].split())
                    else:
                        new_tokens.append(tok)
                cmd_format = " ".join(new_tokens)

            expanded_cmds.append((lineno, cmd_format))

        # ==========================================================
        # 阶段 3：去除所有复杂逻辑，只识别命令名，输出信息
        # ==========================================================
        items: List[Dict[str, str]] = []

        for new_lineno, (orig_lineno, cmd_text) in enumerate(expanded_cmds, start=1):

            tokens = cmd_text.split()
            if not tokens:
                command_name = "UNKNOWN"
            else:
                # 双词命令优先
                if len(tokens) >= 2 and f"{tokens[0]} {tokens[1]}" in CMD_KEYWORDS_MULTI:
                    command_name = f"{tokens[0]} {tokens[1]}"
                elif tokens[0] in CMD_KEYWORDS_SINGLE:
                    command_name = tokens[0]
                else:
                    command_name = "ASSIGN"  # 默认赋值语句

            items.append(
                {
                    "lineno": str(new_lineno),
                    "command": command_name,
                    "text": cmd_text.strip(),
                }
            )

        return items


    def derive_outputs(self, input_file: str, workdir_name: str = "workdir"):
        p = Path(input_file)
        out_dir = p.parent / workdir_name
        out_dir.mkdir(parents=True, exist_ok=True)
        base = p.stem
        out_txt = out_dir / f"{base}.txt"
        out_jsonl = out_dir / f"{base}.jsonl"
        return out_txt, out_jsonl
    

    def pre_main(self, input_file: str, workdir_name: str = "workdir"):
        with open(input_file, "r", encoding="utf-8") as infile:
            lines = infile.readlines()

        items = self.mcl_preprocess(lines)  # List[{"lineno","command","text"}]
        out_txt, out_jsonl = self.derive_outputs(input_file, workdir_name)

        # 1) 写 TXT（每行一个规范化命令）
        with open(out_txt, "w", encoding="utf-8") as ftxt:
            for it in items:
                ftxt.write(it["text"].rstrip() + "\n")

        # 2) 写 JSONL（一行一个 JSON 对象）
        with open(out_jsonl, "w", encoding="utf-8") as fjl:
            for it in items:
                fjl.write(json.dumps(it, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="MCL preprocessor for .m2d files.")
    argparser.add_argument("input_file", help="输入 .m2d 文件路径")
    args = argparser.parse_args()
    preprocessor = M2DPreprocess(rules=PreprocessRules())
    preprocessor.pre_main(args.input_file)
    