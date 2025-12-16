#######################
# core/muti_flows/mcl_preprocess.py
#######################
import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if parent_dir != current_dir:
        current_dir = parent_dir
    else:
        raise FileNotFoundError("未找到项目根目录，请确认项目根目录含 .project_mark 文件")
project_root = current_dir
sys.path.append(project_root)

from src.core_symbol.muti_flows.utils.cmd_dic import CMD_KEYWORDS_MULTI, CMD_KEYWORDS_SINGLE
from src.core_symbol.rules import PreprocessRules, mcl_units

class MCLPreprocess:
    def __init__(self, rules: PreprocessRules):
        self.rules = rules

    # ======================================================
    # Stage 1：注释过滤 + 多行命令合并
    # ======================================================
    def collect_raw_commands(self, input_lines: List[str]) -> List[Tuple[int, str]]:
        """
        返回：[(orig_lineno, merged_command)]
        """
        buffer = ""
        start_lineno = 0
        collected = []

        for i, raw in enumerate(input_lines, start=1):
            if not raw.strip():
                continue
            if raw.strip().startswith(("!", "C ", "Z ")):  # 注释行
                continue

            line = raw.upper()
            stripped = line.split("!")[0].strip()
            if not stripped:
                continue

            if buffer == "":  # start new command
                buffer = stripped
                start_lineno = i
            else:
                buffer += "  " + stripped

            if ";" in stripped:  # command ends
                collected.append((start_lineno, buffer.strip()))
                buffer = ""
                start_lineno = 0

        return collected

    # ======================================================
    # Stage 2：POINT 展开 + 命令过滤 + LINE/AREA 替换
    # ======================================================
    def normalize_scientific_notation(self, text: str) -> str:
        """
        精确识别科学计数法，把大写 E 换成小写 e
        输入本身应是合法科学计数法，不修复断开的 1E - 3
        """
        SCI_PATTERN = re.compile(
            r"""
            (?P<mantissa>[+-]?(?:\d+(?:\.\d*)?|\.\d+))  # 1, 1.0, .3, -2.5
            [eE]                                        # 科学计数法标记
            (?P<exp>[+-]?\d+)                           # +6, -3, 07
            """,
            re.VERBOSE
        )

        def repl(m):
            return f"{m.group('mantissa')}e{m.group('exp')}"
        return SCI_PATTERN.sub(repl, text)



    def expand_macros(self, collected: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
        point_table = {}
        expanded = []

        for lineno, cmd in collected:
            
            cmd = self.normalize_scientific_notation(cmd)

            # 基础格式化
            cmd_format = (
                cmd.replace("=", " = ")
                   .replace(";", " ;")
                   .replace(",", " , ")
                   .replace("**", " ! ")
                   .replace("*", " * ")
                   .replace("!", "**")
            )

            tokens = cmd_format.split()
            if not tokens:
                continue

            first = tokens[0]

            # ---- command filtering ----
            if first in self.rules.commands_to_skip:
                continue

            if first in self.rules.commands_to_skip_byOptions:
                skip_opts = self.rules.commands_to_skip_byOptions[first]
                if any(opt in cmd_format for opt in skip_opts):
                    continue

            if first in self.rules.options_to_skip:
                skip_opts = self.rules.options_to_skip[first]
                possible_opts = self.rules.options_of_command.get(first, [])
                new_tokens = []
                i = 0
                while i < len(tokens):
                    tok = tokens[i]
                    if tok in skip_opts:
                        i += 1
                        while i < len(tokens) and tokens[i] not in possible_opts and tokens[i] != ";":
                            i += 1
                    else:
                        new_tokens.append(tok)
                        i += 1
                cmd_format = " ".join(new_tokens)

            # ---- POINT store ----
            toks = cmd_format.split()
            if not toks:
                continue
            first = toks[0]

            if first == "POINT":
                name = toks[1]
                coords = " ".join(toks[2:-1])  # remove trailing ';'
                point_table[name] = coords

            # ---- POINT substitution for LINE / AREA ----
            if first in ("LINE", "AREA"):
                new_tokens = []
                for tok in toks:
                    if tok in point_table:
                        new_tokens.extend(point_table[tok].split())
                    else:
                        new_tokens.append(tok)
                cmd_format = " ".join(new_tokens)


            expanded.append((lineno, cmd_format))

        return expanded

    # ======================================================
    # Stage 3：只识别命令名、补分号、输出结构化数据
    # ======================================================
    def normalize_commands(self, expanded_cmds: List[Tuple[int, str]]) -> List[Dict[str, str]]:
        items = []

        for new_lineno, (_orig_lineno, cmd) in enumerate(expanded_cmds, start=1):

            text = cmd.strip()
            if not text.endswith(";"):
                text += " ;"

            tokens = text.split()
            command = "ASSIGN"

            if len(tokens) >= 2:
                two = f"{tokens[0]} {tokens[1]}"
                if two in CMD_KEYWORDS_MULTI:
                    command = two
                elif tokens[0] in CMD_KEYWORDS_SINGLE:
                    command = tokens[0]
            else:
                if tokens and tokens[0] in CMD_KEYWORDS_SINGLE:
                    command = tokens[0]

            # function
            if command == "FUNCTION":
                text = (
                    text.replace("+", " + ")
                        .replace("-", " - ")
                        .replace("/", " / ")
                        .replace("(", " ( ")
                        .replace(")", " ) ")
                )

            items.append({
                "lineno": str(new_lineno),
                "command": command,
                "text": text
            })

        return items
    
    # ======================================================
    # Stage 4：单位处理、默认单位补充、单位转换、变量名识别
    # ======================================================
    def process_units(self, items):
        processed = []
        for it in items:
            cmd  = it["command"]
            text = it["text"]
            # print(f"[source]  {text}")
            if cmd == "ASSIGN":                
                text = self.process_assign_units(text)                
            elif cmd == "POINT":                
                text = self.process_point_units(text)                
            elif cmd == "LINE":                
                text = self.process_line_units(text)                
            elif cmd == "AREA":                
                text = self.process_area_units(text)                
            #print(f"[processed]  {text}")
            processed.append({
                "lineno": it["lineno"],
                "command": cmd,
                "text": text,
                "para": {
                    "symbol_name": self.extract_symbol_name(text)
                }
            })
        return processed
    

    def _format_unit(self, text: str) -> str:
        FLOAT_UNIT_PATTERN = re.compile(
        r"(?P<num>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
        r"\s*"
        r"(?P<unit>[A-Za-z_][A-Za-z0-9_]*)"
    )
        """数字 + 单位 → num * unit（幂等）"""
        def repl(m):
            num = m.group("num")
            unit = m.group("unit").rstrip("s")  # 去复数
            return f"{num} * {unit.lower()}"
        return FLOAT_UNIT_PATTERN.sub(repl, text)

    def _ensure_default_unit(self, tokens, skip, default_unit="m"):
        """
        为坐标补充默认单位 m
        skip: 需要跳过的头部 token 数（LINE=2, AREA=3）
        """
        result = tokens.copy()
        i = skip
        for i in range(skip, len(result)):
            tok = result[i]

            # 如果 token 已经有单位（如 "4 * mm" / "4mm"），跳过
            if "*" in tok:
                continue

            # 如果 token 是“数字” → 补默认单位
            if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", tok):
                result[i] = f"{tok} * {default_unit}"

        return result
    
    def extract_symbol_name(self, text: str) -> str | None:
        """
        ASSIGN 或 POINT/LINE/AREA 的第一个 token 通常就是变量名
        """
        tokens = text.split()
        if len(tokens) < 1:
            return None

        # ASSIGN: VAR_NAME = ...
        if "=" in tokens:
            eq_idx = tokens.index("=")
            if eq_idx > 0:
                return tokens[eq_idx - 1]

        # e.g. POINT P1 ...
        # e.g. LINE L2 ...
        # e.g. AREA A3 ...
        if tokens[0].upper() in {"POINT", "LINE", "AREA"} and len(tokens) >= 2:
            return tokens[1]

        return None


    def process_assign_units(self, text: str) -> str:
        """ASSIGN：全文扫描单位"""

        # 预处理下划线连接的数字 + 单位，例如 60_NANOSECONDS
        text = re.sub(
            r'(?P<num>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)_+(?P<unit>[A-Za-z_][A-Za-z0-9_]*)',
            r'\g<num> \g<unit>',
            text
        )
        
        UNIT_PATTERN = "|".join(sorted(mcl_units, key=len, reverse=True))
        ASSIGN_UNIT_PATTERN = re.compile(
            rf"""
            (?P<num>                # 捕获数字
                [+-]?               # 正负号
                (?:\d+\.\d*|\.\d+|\d+)   # 小数 or 整数
                (?:[eE][+-]?\d+)?        # 科学计数法
            )
            \s*                    # 可选空格
            (?P<unit>              # 捕获单位（必须在白名单中）
                (?:{UNIT_PATTERN})s?
            )
            \b
            """,
            re.VERBOSE | re.IGNORECASE
        )
        def repl(m):
            num = m.group("num")
            unit = m.group("unit").lower().rstrip("s")
            return f"{num} * {unit.lower()}"
        return ASSIGN_UNIT_PATTERN.sub(repl, text)
        

    def process_point_units(self, text: str) -> str:
        """POINT <name> x y ... ;"""
        tokens = text.split()
        if len(tokens) <= 2:
            return text

        head = tokens[:2]
        body = tokens[2:]

        body_str = " ".join(body)
        body_str = self._format_unit(body_str)

        return " ".join(head) + " " + body_str


    def process_line_units(self, text: str) -> str:
        """LINE <name> x1 y1 x2 y2 ... ;"""
        tokens = text.split()
        if len(tokens) <= 2:
            return text
        
        tokens = self._ensure_default_unit(tokens, skip=2)

        head = tokens[:2]     # LINE + name
        body = tokens[2:]

        body_str = " ".join(body)
        body_str = self._format_unit(body_str)

        return " ".join(head) + " " + body_str


    def process_area_units(self, text: str) -> str:
        """AREA <name> <option> coords... ;"""
        tokens = text.split()
        if len(tokens) <= 3:
            return text
        
        if tokens[2].upper() == "RECT":
            tokens[2] = "RECTANGULAR"
        
        tokens = self._ensure_default_unit(tokens, skip=3)

        head = tokens[:3]     # AREA + name + option
        body = tokens[3:]

        body_str = " ".join(body)
        body_str = self._format_unit(body_str)

        return " ".join(head) + " " + body_str
    
    # ======================================================
    # Stage 5: 处理 SYS$xxx 引用
    # ======================================================
    def mark_sys_refs(self, items: List[Dict]) -> List[Dict]:
        """
        规则：
        1) 某条命令出现 SYS$ → 本条 ignore=yes
        2) 取本条 para.symbol_name
        3) 再扫一遍：凡是文本中使用了这个 symbol_name 的命令，也 ignore=yes
        """

        import re
        SYS_PATTERN = re.compile(r"SYS\$", re.IGNORECASE)

        # Step 1: 找出所有出现 SYS$ 的条目及其 symbol_name
        bad_symbols = set()

        for it in items:
            text = it.get("text", "")
            para = it.setdefault("para", {})

            if SYS_PATTERN.search(text):  # 本条带 SYS$xxx
                para["ignore"] = "yes"

                sym = para.get("symbol_name")
                if sym:
                    bad_symbols.add(sym.upper())  # 记录本条命令自己的变量名

        if not bad_symbols:
            return items  # 没有 SYS$，提前返回

        # Step 2: 再扫描谁引用了这些 symbol
        for it in items:
            text = it.get("text", "")
            para = it.setdefault("para", {})

            # 只要文本里出现某坏符号，就忽略
            for sym in bad_symbols:
                # 用 \b 保证是完整词匹配，不会误匹配比如 ABC 和 ABCD
                if re.search(rf"\b{sym}\b", text, re.IGNORECASE):
                    para["ignore"] = "yes"
                    break  # 一个匹配就够了

        return items


    # ======================================================
    # 总入口：三阶段流水线
    # ======================================================
    def mcl_preprocess(self, input_lines: List[str]) -> List[Dict[str, str]]:
        s1 = self.collect_raw_commands(input_lines)
        s2 = self.expand_macros(s1)
        s3 = self.normalize_commands(s2)
        s4 = self.process_units(s3)
        s5 = self.mark_sys_refs(s4)
        
        return s5

    # ======================================================
    # 输出处理
    # ======================================================
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

        items = self.mcl_preprocess(lines)
        out_txt, out_jsonl = self.derive_outputs(input_file, workdir_name)

        with open(out_txt, "w", encoding="utf-8") as ftxt:
            for it in items:
                ftxt.write(it["text"].rstrip() + "\n")

        with open(out_jsonl, "w", encoding="utf-8") as fjl:
            for it in items:
                fjl.write(json.dumps(it, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    """
    argparser = argparse.ArgumentParser(description="MCL preprocessor for .m2d files.")
    argparser.add_argument("input_file", help="输入 .m2d 文件路径")
    args = argparser.parse_args()
    """
    preprocessor = MCLPreprocess(rules=PreprocessRules())
    res = preprocessor.process_assign_units("A = 1.05VOLTS")
    print(res)
