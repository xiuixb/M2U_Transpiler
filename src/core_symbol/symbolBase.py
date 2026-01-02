"""
符号基类 (Symbol Base Class)
==========================

符号基类是整个符号系统的核心基础类，负责表示和处理各种类型的符号。
在M2U_Transpiler中，符号代表从MAGIC MCL语言到UNIPIC配置文件转换过程中的各种元素。

符号的生命周期包括：
1. 源文本 (source text) - 原始MAGIC MCL代码
2. 清洗文本 (cleaned text) - 经过预处理的MCL代码
3. 中间文本 (intermediate text) - 解析后的中间表示
4. 目标文本 (target text) - 最终的UNIPIC配置文件

符号类型包括：
- 源符号表 (magic_symTable) - MAGIC中的符号定义
- 中间符号表 (mid_symTable) - 中间转换过程中的符号
- 目标符号表 (unipic25d_symTable) - UNIPIC中的符号定义
"""

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

from dataclasses import dataclass, field
from typing import Any, Dict, List

class MagicMCLSymbol():
    """
    MAGIC源文本符号类，表示MAGIC MCL语言中的单条命令
    """
    def __init__(self, content: str, filename: str = '', domain: str = '', semantics: str = ''):
        self.content = content
        self.filename = filename
        self.semantics = semantics
        self.type = "MCL"

class MagicM2DSymbol():
    """
    MAGIC源文本符号类，表示MAGIC M2D文件
    """
    def __init__(self, content: List[str], filename: str = '', domain: str = '', semantics: str = ''):
        self.content = content
        self.filename = filename
        self.semantics = semantics
        self.type = "M2D"

class MagicCMDSymbol():
    """
    MAGIC清洗文本符号类，表示MAGIC清洗后的单条命令
    """
    def __init__(self, content: str, filename: str = '', domain: str = '', semantics: str = ''):
        self.content = content
        self.filename = filename
        self.semantics = semantics
        self.type = "CMD"

class MagicTXTSymbol():
    """
    MAGIC清洗文本符号类，表示MAGIC清洗后的文本
    """
    def __init__(self, content: List[str], filename: str = '', domain: str = '', semantics: str = ''):
        self.content = content
        self.filename = filename
        self.semantics = semantics
        self.type = "TXT"


@dataclass
class ParseResult:
    """
    解析器统一返回的内部对象（仅在内存流转；最终会被转换为对外 dict）。
    属性字段：
        lineno     : 过滤后行号（预处理/路由决定）
        command     : 命令关键字（如 "LINE"/"AREA"/"EMISSION"...）
        payload     : 语义结果（供转换器使用）
        parser_kind : 解析器名（"PLY"|"REGEX"|"LLM" 或自定义）
        ok          : 是否成功解析出语义结果
        errors      : 错误信息字符串，"no"表示无错误
        text        : 原始单行命令文本（规范化后的）
    """
    lineno: int
    command: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    parser_kind: str = ""
    ok: bool = False
    errors: str = "no"
    text: str = ""


class MagicSymbolTable():
    """
    MAGIC符号表类，表示MAGIC解析出来的符号表
    """
    def __init__(self):
        self.cmds_list: List = []
        self.props = {}

    def load_list(self, cmds_list: List):
        self.cmds_list = cmds_list


class MidSymbolTable():
    """
    中间符号表类，表示MAGIC符号表一轮转换后的符号表
    """
    def __init__(self):
        self.props = {}
        self.symbol_table = {}
        self.functions = {}
        self.geom: Dict[str, Dict[str, Any]] = {
            "points": {},    # name -> (qx, qy)
            "lines": {},     # name -> [(qx, qy), ...]
            "areas": {},     # name -> {"type": a_type, "points": [(qx,qy),...], ...}
        }
        self.grid = {'X1': -1.0, 'X2': -1.0, 'X3': -1.0}
        self.ports = {}
        self.emits = []
    
        self.presets = {}
        self.inductor = []
        self.foilModel = []
        self.freespace = []

        self.observes = []
        self.FieldsDgn = []
        self.timers = {}
        

        self.void_area = {}
        self.area_entities = {}
        self.geom_other_entity = {}
        self.result = {}
        

class Unipic25dSymbolTable():
    """
    UNIPIC2.5D符号表类，表示中间符号表经过转换后的符号表
    """
    def __init__(self):
        self.buildIn = []
        self.FaceBndIn = []
        self.PtclSourcesIn = []
        self.SpeciesIn = []
        self.PMLIn = []
        self.StaticNodeFLdsIn = []
        self.CircuitModelIn = []
        self.GlobalSettingIn = []
        self.FieldsDgnIn = []

        

class Unipic25dInFiles():
    """
    UNIPIC2.5D输入文件类，表示UNIPIC2.5D配置文件
    """
    def __init__(self, dirname: str = ''):
        self.dirname = dirname
        self.type = "INFILE"


class Unipic25dProject():
    """
    UNIPIC2.5D项目类，表示UNIPIC2.5D项目
    """
    def __init__(self):
        self.type = "PROJECT"
        self.symbol_table = {}
        self.void_area = {}
        self.selection = []
        


# 测试代码
if __name__ == "__main__":
    pass