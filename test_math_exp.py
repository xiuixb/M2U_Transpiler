import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, r'd:\AAA_PIC\Parser\M2U_Transpiler')

from src.core_symbol.muti_flows.mcl_preprocess import MCLPreprocess
from src.core_symbol.rules import PreprocessRules

# 创建预处理器实例
preprocessor = MCLPreprocess(rules=PreprocessRules())

# 测试math_exp_format函数
test_cases = [".01m", "8.9cm", ".24m", "7.9cm"]

print("测试math_exp_format函数:")
for case in test_cases:
    try:
        result = preprocessor.math_exp_format(case)
        print(f"  {case} -> {result}")
    except Exception as e:
        print(f"  {case} -> 错误: {e}")

# 测试float_ext_exp正则表达式
import re
print("\n测试float_ext_exp正则表达式:")
for case in test_cases:
    if re.match(preprocessor.rules.float_ext_exp, case):
        print(f"  {case} -> 匹配")
    else:
        print(f"  {case} -> 不匹配")