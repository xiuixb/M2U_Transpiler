import sys
import os
import re

# 添加项目根目录到Python路径
sys.path.insert(0, r'd:\AAA_PIC\Parser\M2U_Transpiler')

from core.muti_flows.mcl_preprocess import MCLPreprocess
from core.rules import PreprocessRules

# 创建预处理器实例
preprocessor = MCLPreprocess(rules=PreprocessRules())

# 模拟阶段2处理POINT命令的过程
def simulate_stage2_point_processing():
    print("模拟阶段2处理POINT命令:")
    
    # 原始命令
    cmd = "POINT B_PROBE_INLET  .01m,8.9cm ;"
    print(f"原始命令: {cmd}")
    
    # 格式化命令
    cmd_format = preprocessor.replace_all(cmd, "=", " = ")
    cmd_format = preprocessor.replace_all(cmd_format, ";", " ;")
    cmd_format = preprocessor.replace_all(cmd_format, ",", " , ")
    print(f"格式化后: {cmd_format}")
    
    # 分割token
    toks = cmd_format.split()
    print(f"Token分割: {toks}")
    
    if toks and toks[0] == "POINT":
        name = toks[1]
        coords = " ".join(toks[2:-1])  # 去掉末尾 ;
        print(f"坐标部分: {coords}")
        
        # 对坐标单位进行格式化处理
        coord_tokens = coords.split()
        formatted_coords = []
        for token in coord_tokens:
            print(f"  处理token: '{token}'")
            if re.match(preprocessor.rules.float_ext_exp, token):
                try:
                    formatted_token = preprocessor.math_exp_format(token)
                    print(f"    格式化后: '{formatted_token}'")
                    formatted_coords.append(formatted_token)
                except ValueError as e:
                    print(f"    格式化错误: {e}")
                    formatted_coords.append(token)
            else:
                formatted_coords.append(token)
        
        coords = " ".join(formatted_coords)
        print(f"格式化后的坐标: {coords}")
        
        return f"POINT {name} {coords} ;"
    
    return cmd

# 运行模拟
result = simulate_stage2_point_processing()
print(f"\n最终结果: {result}")