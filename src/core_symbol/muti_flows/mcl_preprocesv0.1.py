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


class MCLPreprocess:
    def __init__(self, rules: PreprocessRules):
        self.rules = rules
    
    # ---------- 小工具 ----------
    def replace_all(self, text, from_str, to_str):
        return text.replace(from_str, to_str)

    def math_exp_split(self, mexp):
        res = ""
        while mexp:
            match = re.search(self.rules.float_exp, mexp)
            if match:
                exp = mexp[:match.start()]
                res += exp.replace("+", " + ").replace("-", " - ")
                res += match.group(0)
                mexp = mexp[match.end():]
            else:
                res += mexp.replace("+", " + ").replace("-", " - ")
                mexp = ""
        return res

    def math_exp_format(self, mexp):
        """单位保持小写"""
        if not mexp:
            return ""
        mexp = mexp.lower()
        mexp = re.sub(self.rules.float_exp, r' \g<0> ', mexp)
        mexp = mexp.replace("_", " ")
        units = [
            ("atto", " atto "), ("femto", " femto "), ("pico", " pico "),
            ("nano", " nano "), ("micro", " micro "), ("milli", " milli "),
            ("centi", " centi "), ("deci", " deci "), ("kilo", " kilo "),
            ("mega", " mega "), ("giga", " giga "), ("tera", " tera "),
            ("peta", " peta "), ("exa", " exa "),
        ]
        for old, new in units:
            mexp = mexp.replace(old, new)
        #print("[unit:]",mexp)
        parts = mexp.split()
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            parts[1] = parts[1].rstrip('s')
            return parts[0] + " * " + parts[1]
        elif len(parts) == 3:
            parts[2] = parts[2].rstrip('s')
            return parts[0] + " * " + parts[1] + parts[2]
        else:
            raise ValueError(f"预处理阶段-单位处理：无法处理的数学表达式：{mexp}, 写法与预期不符")
        

    def ensure_units(self, values: List[str], default_unit="M") -> List[str]:
        """
        确保数值列表都带单位；纯数字→补 '*{default_unit}'（注意：你原来是直接拼 {val}{default_unit}，这里保持一致性）
        """
        processed = []
        for val in values:
            val = val.strip()
            if "*" in val:  # 已经带单位
                processed.append(val)
            else:
                try:
                    _ = float(val)
                    processed.append(f"{val}*{default_unit.lower()}")  # 规范为 "*m"
                except ValueError:
                    processed.append(val)
        return processed

    def process_line_command(self, cmd: str, default_unit="M") -> str:
        clean_cmd = cmd.replace(",", " ")
        clean_cmd = re.sub(r"\s*\*\s*", "*", clean_cmd)
        tokens = clean_cmd.split()
        if len(tokens) >= 5:  # LINE name ... x1 y1 x2 y2 ;
            coords = tokens[-5:-1]
            coords = self.ensure_units(coords, default_unit=default_unit)
            tokens = tokens[:-5] + coords
            if tokens[-1] != ";":
                tokens.append(";")
        return " ".join(tokens)

    def process_area_command(self, cmd: str, default_unit="M") -> str:
        clean_cmd = cmd.replace(",", " ")
        clean_cmd = re.sub(r"\s*\*\s*", "*", clean_cmd)
        tokens = clean_cmd.split()
        coords = [t for t in tokens if re.match(self.rules.float_ext_exp, t)]
        coords = self.ensure_units(coords, default_unit=default_unit)
        idx = 0
        for i, t in enumerate(tokens):
            if re.match(self.rules.float_ext_exp, t):
                tokens[i] = coords[idx]
                idx += 1
        return " ".join(tokens)

    # ---------- 主流程 ----------
    def mcl_preprocess(self, input_lines: List[str]) -> List[Dict[str, str]]:
        """
        返回：[
        {"lineno": <过滤后顺序号>, "command": <命令名>, "text": <完整单行命令>},
        ...
        ]
        """
        # ========= 阶段 1：注释处理 + 收集单行命令（记录起始行号） =========
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
            if buffer == "":
                buffer = stripped
                start_lineno = i
            else:
                buffer += " inline_enter " + stripped
            if ";" in stripped:
                collected.append((start_lineno, buffer.strip()))
                buffer = ""
                start_lineno = 0

        # ========= 阶段 2：宏展开（POINT表）、过滤/裁剪 =========
        point_table: Dict[str, str] = {}
        expanded_cmds: List[Tuple[int, str]] = []  # [(orig_lineno, cmd_after_macro)]
        for lineno, cmd in collected:
            cmd_format = self.replace_all(cmd, "=", " = ")
            cmd_format = self.replace_all(cmd_format, ";", " ;")
            cmd_format = self.replace_all(cmd_format, ",", " , ")
            tokens = cmd_format.split()
            if not tokens:
                continue
            first = tokens[0]

            # 过滤
            if first in self.rules.commands_to_skip:
                continue
            if first in self.rules.commands_to_skip_byOptions:
                skip_opts = self.rules.commands_to_skip_byOptions[first]
                if any(opt in cmd_format for opt in skip_opts):
                    continue
            if first in self.rules.options_to_skip:
                skip_opts = self.rules.options_to_skip[first]
                possible_opts = self.rules.options_of_command.get(first, [])
                tokens = cmd_format.split()
                new_tokens = []
                i = 0
                while i < len(tokens):
                    tok = tokens[i]
                    if tok in skip_opts:
                        i += 1
                        while i < len(tokens) and tokens[i] not in possible_opts and tokens[i] != ";":
                            i += 1
                    else:
                        new_tokens.append(tok); i += 1
                cmd_format = " ".join(new_tokens)

            # POINT 展开
            toks = cmd_format.split()
            if not toks:
                continue
            first = toks[0]
            if first == "POINT":
                name = toks[1]
                coords = " ".join(toks[2:-1])  # 去掉末尾 ;
                point_table[name] = coords

            if first in ("LINE", "AREA"):
                new_tokens = []
                for tok in toks:
                    if tok in point_table:
                        new_tokens.extend(point_table[tok].split())
                    else:
                        new_tokens.append(tok)
                cmd_format = " ".join(new_tokens)

            expanded_cmds.append((lineno, cmd_format))

        # ========= 阶段 3：字符/单位处理，Tokenizer，单位归一 =========
        items: List[Dict[str, str]] = []
        for new_lineno, (_orig_lineno, cmd) in enumerate(expanded_cmds, start=1):
            full_cmd = self.math_exp_split(cmd)
            if full_cmd.startswith("LINE"):
                full_cmd = self.process_line_command(full_cmd)
            elif full_cmd.startswith("AREA"):
                full_cmd = self.process_area_command(full_cmd)

            full_cmd = self.replace_all(full_cmd, "**", " ! ")
            full_cmd = self.replace_all(full_cmd, "*", " * ")
            full_cmd = self.replace_all(full_cmd, "!", "**")
            full_cmd = self.replace_all(full_cmd, "/", " / ")
            full_cmd = self.replace_all(full_cmd, "(", " ( ")
            full_cmd = self.replace_all(full_cmd, ")", " ) ")
            full_cmd = self.replace_all(full_cmd, ",", " , ")
            full_cmd = self.replace_all(full_cmd, ";", " ; ")

            tokenizer = Tokenizer(full_cmd, " \t\n\r\f")
            tokens = tokenizer.split()
            for i, token in enumerate(tokens):
                if re.match(self.rules.float_ext_exp, token):
                    tokens[i] = self.math_exp_format(token)

            text = " ".join(tokens)
            text = self.replace_all(text, " inline_enter ", " ")
            text = re.sub(r";\s*;", ";", text).strip()
            if not text.endswith(";"):
                text += " ;"

            cmd_tokens = text.split()



            # ---- 多词命令优先匹配 ----
            command_name = "ASSIGN"  # 默认视为赋值语句
            if len(cmd_tokens) >= 2:
                first_two = f"{cmd_tokens[0].upper()} {cmd_tokens[1].upper()}"
                if first_two in CMD_KEYWORDS_MULTI:
                    command_name = first_two
                elif cmd_tokens[0].upper() in CMD_KEYWORDS_SINGLE:
                    command_name = cmd_tokens[0].upper()
            else:
                # 单token情况
                first_token = cmd_tokens[0].upper() if cmd_tokens else "UNKNOWN"
                if first_token in CMD_KEYWORDS_SINGLE:
                    command_name = first_token



            items.append({
                "lineno": str(new_lineno),   # 或保留为 int：new_lineno
                "command": command_name,
                "text": text
            })
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
    preprocessor = MCLPreprocess(rules=PreprocessRules())
    preprocessor.pre_main(args.input_file)
    