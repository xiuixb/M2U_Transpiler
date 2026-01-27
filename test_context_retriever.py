#!/usr/bin/env python3
"""
测试上下文检索器功能
"""

import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.core_symbol.symbolBase import MidSymbolTable
from src.core_cac.dependency_retriever import DependencyRetriever

def setup_test_data():
    """设置测试数据"""
    mid_symbols = MidSymbolTable()
    
    # 添加测试变量
    mid_symbols.variable["DR"] = {
        "var_name": "DR",
        "parameters": {
            "var_expr": "0.5 * mm"
        },
        "cac_result": {
            "var_num": "0.5",
            "var_unit": "mm"
        },
        "dependencies": []
    }
    
    mid_symbols.variable["H_board"] = {
        "var_name": "H_board", 
        "parameters": {
            "var_expr": "51.0 * mm"
        },
        "cac_result": {
            "var_num": "51.0",
            "var_unit": "mm"
        },
        "dependencies": []
    }
    
    mid_symbols.variable["B_board"] = {
        "var_name": "B_board",
        "parameters": {
            "var_expr": "H_board - 2mm"
        },
        "cac_result": {
            "var_num": "49.0",
            "var_unit": "mm"
        },
        "dependencies": [{"sys_type": "variable", "sys_name": "H_board"}]
    }
    
    # 添加测试函数
    mid_symbols.function["FIN"] = {
        "func_name": "FIN",
        "parameters": {
            "func_params": ["T"],
            "func_body": "VOLTAGE.MAX * MAX(0.0, MIN(1.0, T / TRISE))"
        },
        "cac_result": {
            "func_vars": [
                {"VOLTAGE.MAX": 500000.0},
                {"TRISE": 1e-09}
            ]
        }
    }
    
    # 添加测试点
    mid_symbols.geometry["point"]["POINT1"] = (0.0, 51.0)  # 使用H_board
    mid_symbols.geometry["point"]["POINT2"] = (60.0, 25.0)
    
    # 添加测试线
    mid_symbols.geometry["line"]["LINE1"] = [(0.0, 0.0), (60.0, 25.0)]  # 使用POINT2
    mid_symbols.geometry["line"]["INLET"] = [(0.0, 25.0), (0.0, 0.0)]
    
    # 添加测试面
    mid_symbols.geometry["area"]["CATHODE"] = {
        "type": "POLYGONAL",
        "points": [(0.0, 51.0), (57.0, 51.0), (57.0, 49.0), (0.0, 49.0)]  # 使用H_board和B_board的值
    }
    
    # 添加测试端口
    mid_symbols.ports["port1"] = {
        "kind": "MurVoltagePort",
        "geom_name": "INLET",  # 依赖LINE
        "direction": "POSITIVE",
        "result": "VOLTAGE_MAX*max(0.0,min(1.0,t/TRISE))",  # 依赖函数FIN
        "func_vars": [{"VOLTAGE_MAX": 500000.0}, {"TRISE": 1e-09}]
    }
    
    # 设置命令文本存储
    command_texts = {
        "DR": "VARIABLE DR = 0.5 * mm",
        "H_board": "VARIABLE H_board = 51.0 * mm", 
        "B_board": "VARIABLE B_board = H_board - 2mm",
        "FIN": "FUNCTION FIN(T) = VOLTAGE.MAX * MAX(0.0, MIN(1.0, T / TRISE))",
        "POINT1": "POINT POINT1 = 0.0mm, H_board",
        "POINT2": "POINT POINT2 = 60.0mm, 25.0mm",
        "LINE1": "LINE LINE1 = 0.0, 0.0, POINT2",
        "INLET": "LINE INLET = 0.0, 25.0, 0.0, 0.0",
        "CATHODE": "AREA CATHODE POLYGONAL 0.0, H_board, 57.0mm, H_board, 57.0mm, B_board, 0.0, B_board",
        "port1": "PORT INLET POSITIVE INCOMING FIN E1 G1 E2 G2 NORMALIZATION VOLTAGE INLET"
    }
    
    return mid_symbols, command_texts

def test_basic_dependency():
    """测试基本依赖检索"""
    print("=" * 60)
    print("测试基本依赖检索")
    print("=" * 60)
    
    mid_symbols, command_texts = setup_test_data()
    retriever = DependencyRetriever()
    retriever.load_context(mid_symbols, command_texts)
    
    # 测试变量依赖
    print("\n1. 测试变量B_board的依赖（应该依赖H_board）:")
    command_text = "VARIABLE B_board = H_board - 2mm"
    dependencies = retriever.get_dependency_item("variable", command_text)
    print(f"   命令: {command_text}")
    print(f"   依赖数量: {len(dependencies)}")
    for i, dep in enumerate(dependencies):
        print(f"   依赖{i+1}: {dep}")
    
    return len(dependencies) > 0

def test_geometry_dependency():
    """测试几何依赖检索"""
    print("\n" + "=" * 60)
    print("测试几何依赖检索")
    print("=" * 60)
    
    mid_symbols, command_texts = setup_test_data()
    retriever = DependencyRetriever()
    retriever.load_context(mid_symbols, command_texts)
    
    # 测试点依赖变量
    print("\n1. 测试点POINT1的依赖（应该依赖变量H_board）:")
    command_text = "POINT POINT1 = 0.0mm, H_board"
    dependencies = retriever.get_dependency_item("point", command_text)
    print(f"   命令: {command_text}")
    print(f"   依赖数量: {len(dependencies)}")
    for i, dep in enumerate(dependencies):
        print(f"   依赖{i+1}: {dep}")
    
    # 测试线依赖点
    print("\n2. 测试线LINE1的依赖（应该依赖点POINT2）:")
    command_text = "LINE LINE1 = 0.0, 0.0, POINT2"
    dependencies = retriever.get_dependency_item("line", command_text)
    print(f"   命令: {command_text}")
    print(f"   依赖数量: {len(dependencies)}")
    for i, dep in enumerate(dependencies):
        print(f"   依赖{i+1}: {dep}")
    
    # 测试面依赖变量（递归依赖）
    print("\n3. 测试面CATHODE的依赖（应该递归依赖H_board和B_board）:")
    command_text = "AREA CATHODE POLYGONAL 0.0, H_board, 57.0mm, H_board, 57.0mm, B_board, 0.0, B_board"
    dependencies = retriever.get_dependency_item("area", command_text)
    print(f"   命令: {command_text}")
    print(f"   依赖数量: {len(dependencies)}")
    for i, dep in enumerate(dependencies):
        print(f"   依赖{i+1}: {dep}")
    
    return len(dependencies) > 0

def test_port_dependency():
    """测试端口依赖检索"""
    print("\n" + "=" * 60)
    print("测试端口依赖检索")
    print("=" * 60)
    
    mid_symbols, command_texts = setup_test_data()
    retriever = DependencyRetriever()
    retriever.load_context(mid_symbols, command_texts)
    
    # 测试端口依赖（应该依赖线和函数）
    print("\n1. 测试端口port1的依赖（应该依赖线INLET和函数FIN）:")
    command_text = "PORT INLET POSITIVE INCOMING FIN E1 G1 E2 G2 NORMALIZATION VOLTAGE INLET"
    dependencies = retriever.get_dependency_item("port", command_text)
    print(f"   命令: {command_text}")
    print(f"   依赖数量: {len(dependencies)}")
    for i, dep in enumerate(dependencies):
        print(f"   依赖{i+1}: {dep}")
    
    return len(dependencies) > 0

def test_dependency_summary():
    """测试依赖关系摘要"""
    print("\n" + "=" * 60)
    print("测试依赖关系摘要")
    print("=" * 60)
    
    mid_symbols, command_texts = setup_test_data()
    retriever = DependencyRetriever()
    retriever.load_context(mid_symbols, command_texts)
    
    # 获取复杂命令的依赖摘要
    command_text = "AREA CATHODE POLYGONAL 0.0, H_board, 57.0mm, H_board, 57.0mm, B_board, 0.0, B_board"
    summary = retriever.get_dependency_summary("area", command_text)
    
    print(f"   命令类型: {summary['command_type']}")
    print(f"   命令文本: {summary['command_text']}")
    print(f"   依赖类型: {summary['dependency_types']}")
    print(f"   依赖数量: {summary['dependency_count']}")
    print("   依赖详情:")
    for i, dep in enumerate(summary['dependencies']):
        print(f"     {i+1}. {dep}")
    
    return summary['dependency_count'] > 0

def test_circular_dependency():
    """测试循环依赖处理"""
    print("\n" + "=" * 60)
    print("测试循环依赖处理")
    print("=" * 60)
    
    mid_symbols = MidSymbolTable()
    
    # 创建循环依赖的测试数据
    mid_symbols.variable["A"] = {
        "var_name": "A",
        "parameters": {"var_expr": "B + 1"},
        "cac_result": {},
        "dependencies": []
    }
    
    mid_symbols.variable["B"] = {
        "var_name": "B", 
        "parameters": {"var_expr": "A + 2"},
        "cac_result": {},
        "dependencies": []
    }
    
    command_texts = {
        "A": "VARIABLE A = B + 1",
        "B": "VARIABLE B = A + 2"
    }
    
    retriever = DependencyRetriever()
    retriever.load_context(mid_symbols, command_texts)
    
    print("\n1. 测试循环依赖A->B->A:")
    command_text = "VARIABLE A = B + 1"
    dependencies = retriever.get_dependency_item("variable", command_text)
    print(f"   命令: {command_text}")
    print(f"   依赖数量: {len(dependencies)}")
    for i, dep in enumerate(dependencies):
        print(f"   依赖{i+1}: {dep}")
    
    print("   ✅ 循环依赖处理正常（应该避免无限递归）")
    return True

if __name__ == "__main__":
    print("🔍 上下文检索器功能测试")
    print("=" * 80)
    
    tests = [
        ("基本依赖检索", test_basic_dependency),
        ("几何依赖检索", test_geometry_dependency), 
        ("端口依赖检索", test_port_dependency),
        ("依赖关系摘要", test_dependency_summary),
        ("循环依赖处理", test_circular_dependency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 运行测试: {test_name}")
            if test_func():
                print(f"✅ {test_name} - 通过")
                passed += 1
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！上下文检索器工作正常")
    else:
        print("⚠️  部分测试失败，需要进一步调试")
    
    print("=" * 80)