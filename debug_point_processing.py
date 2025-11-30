import sys
import os
import re

# 添加项目根目录到Python路径
sys.path.insert(0, r'd:\AAA_PIC\Parser\M2U_Transpiler')

from core.muti_flows.mcl_preprocess import MCLPreprocess
from core.rules import PreprocessRules

# 创建预处理器实例
preprocessor = MCLPreprocess(rules=PreprocessRules())

# 模拟完整的预处理流程，但添加调试信息
def debug_preprocess():
    # 模拟输入行
    input_lines = [
        "! Test POINT command unit processing issue\n",
        "POINT B_PROBE_INLET  .01m , 8.9cm ;\n",
        "POINT B_PROBE_OUTLET .24m , 7.9cm ;\n"
    ]
    
    print("=== 阶段 1：注释处理 + 收集单行命令 ===")
    buffer = ""
    start_lineno = 0
    collected = []
    for i, raw in enumerate(input_lines, start=1):
        print(f"处理行 {i}: {repr(raw)}")
        if not raw.strip():
            continue
        if raw.strip().startswith(("!", "C ", "Z ")):
            print(f"  跳过注释行")
            continue
        line = raw.upper()
        print(f"  转换为大写: {repr(line)}")
        stripped = line.split("!")[0].strip()
        if not stripped:
            continue
        if buffer == "":
            buffer = stripped
            start_lineno = i
        else:
            buffer += " inline_enter " + stripped
        if ";" in stripped:
            print(f"  收集命令: {buffer.strip()}")
            collected.append((start_lineno, buffer.strip()))
            buffer = ""
            start_lineno = 0
    
    print(f"\n收集到的命令: {collected}")
    
    print("\n=== 阶段 2：宏展开（POINT表）、过滤/裁剪 ===")
    point_table = {}
    expanded_cmds = []
    for lineno, cmd in collected:
        print(f"\n处理命令: {repr(cmd)}")
        cmd_format = preprocessor.replace_all(cmd, "=", " = ")
        cmd_format = preprocessor.replace_all(cmd_format, ";", " ;")
        cmd_format = preprocessor.replace_all(cmd_format, ",", " , ")
        print(f"格式化后: {repr(cmd_format)}")
        
        tokens = cmd_format.split()
        if not tokens:
            continue
        first = tokens[0]

        # POINT 展开
        toks = cmd_format.split()
        if not toks:
            continue
        first = toks[0]
        if first == "POINT":
            name = toks[1]
            coords = " ".join(toks[2:-1])  # 去掉末尾 ;
            print(f"POINT命令 - 名称: {name}, 坐标: {repr(coords)}")
            # 对坐标单位进行格式化处理
            coord_tokens = coords.split()
            formatted_coords = []
            for token in coord_tokens:
                print(f"  处理坐标token: '{token}'")
                if re.match(preprocessor.rules.float_ext_exp, token):
                    try:
                        formatted_token = preprocessor.math_exp_format(token)
                        print(f"    格式化后: '{formatted_token}'")
                        formatted_coords.append(formatted_token)
                    except ValueError:
                        formatted_coords.append(token)
                else:
                    formatted_coords.append(token)
            coords = " ".join(formatted_coords)
            print(f"  格式化后的坐标: {coords}")
            point_table[name] = coords

        expanded_cmds.append((lineno, cmd_format))
    
    print(f"\nPOINT表: {point_table}")
    print(f"展开后的命令: {expanded_cmds}")

# 运行调试
debug_preprocess()