"""
==========================
src/domain/config/symbolBase.py
==========================
符号基类是整个符号系统的核心基础类，负责表示和处理各种类型的符号。
在M2U_Transpiler中，符号代表从MAGIC MCL语言到UNIPIC配置文件转换过程中的各种元素。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ParseResult:
    """
    解析器统一返回的内部对象（仅在内存流转；最终会被转换为对外 dict）。
    属性字段：
        lineno     : 过滤后行号（预处理/路由决定）
        command     : 命令关键字（如 "LINE"/"AREA"/"EMISSION"...）
        sys_name    : 定义的语义名称
        payload     : 语义结果（供转换器使用）
        parser_kind : 解析器名（"PLY"|"REGEX"|"LLM" 或自定义）
        ok          : 是否成功解析出语义结果
        errors      : 错误信息字符串，"no"表示无错误
        text        : 原始单行命令文本（规范化后的）
    """
    lineno: int
    command: str = ""
    sys_name: str = ""
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
    基于样例文件重构，支持完整的中间表示结构
    """
    def __init__(self):

        self.index = ['selection', 'material_assign', 'user_defined_material', 'particle_library', 'field_excitation', 'emission', 'secondary_electron_emitter', 'electromagnetic_field', 'inductor', 'resistor', 'foil_model', 'diagnostic']

        # 元数据
        self.sT = {

            "meta": {
                "version": "1.0",
                "source_file": "",
                "target_format": "unipic2.5d", 
                "creation_time": "",
                "device_type": "",
                "unit": "mm",
                "coordinate_system_1": "Z",
                "coordinate_system_2": "R",
                "OCAF_Material": {
                    "PEC": "理想导体",
                    "FREESPACE": "自由空间", 
                    "USERDEFINED": "用户定义材料",
                    "OPENPORT": "开放端口, PML 截断边界", 
                    "MURPORT": "MUR端口, Mur 吸收边界", 
                    "INPUTPORT": "输入端口, PML 截断边界", 
                    "INPUTMURPORT": "输入端口, MUR 吸收边界",
                    "EMBEDDEDPORT": "嵌入端口", 
                    "PECPORT": "PEC端口", 
                    "COMMONPLANE": "", 
                    "EMITTER": "带电粒子发射边界"
                }
            },
            
            # 变量定义
            "variable": {},
            
            # 函数定义  
            "function": {},
            
            # 几何定义
            "geometry": {
                "point": {},
                "line": {},
                "area": {},
                "area_cac_result": {},
                "selection": []
            },
            
            # 网格定义
            "mesh": {
                "mark": [],
                "dx1": {},
                "dx2": {}
            },
            
            # 材料定义
            "materials": {
                "PMLSetting": {
                    "material_type": "PMLSetting",
                    "parameters": {
                        "key": 1,
                        "powerOrder": 3,
                        "alpha": 0.0,
                        "kappaMax": 40.0,
                        "sigmaRatio": 7.5
                    }
                },
                "material_library": {
                    "PEC": {
                        "material_type": "PEC",
                        "dependencies": [],
                        "parameters": {}
                    },
                    "FREESPACE": {
                        "material_type": "FREESPACE",
                        "dependencies": [],
                        "parameters": {}
                    },
                    "user_defined_material": []
                },
                "material_assign": []
            },
            
            # 边界条件
            "boundaries": {
                "port": []
            },
            
            # 物理实体
            "physics_entities": {
                "particle_library": [
                    {
                        "species_name": "ELECTRON",
                        "parameters": {
                            "charge": -1.6022e-19,
                            "mass": 9.109e-31
                        }
                    }
                ],
                "field_excitation": [],
                "emission_model": [],
                "emit_apply": [],
                "secondary_electron_emitter": [],
                "electromagnetic_field": [],
                "inductor": [],
                "resistor": [],
                "foil_model": []
            },
            
            # 诊断
            "diagnostic": [],

            # test
            "test": [],
            
            # 全局设置
            "global_settings": {
                "time_step": "1e-12",
                "simulation_time": "1e-9",
                "particle_parameters": {
                    "species_name": "ELECTRON",
                    "parameters": {
                        "ptclCreationRate": 3.0,
                        "macro_particle_particle_number": 1000000,
                        "emitter_boundary": "port2"
                    },
                    "cac_result": {}
                }
            }
        }
        
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于JSON序列化"""
        return self.sT
    
    def test_dict(self):
        """测试转换为字典格式"""
        return {
            "variable": self._first_item(self.sT["variable"]),
            "function": self._first_item(self.sT["function"]),
            "point": self._first_item(self.sT["geometry"]["point"]),
            "line": self._first_item(self.sT["geometry"]["line"]),
            "area": self._first_item(self.sT["geometry"]["area"]),
            "other_geometry": {
                "area_cac_result": self.sT["geometry"]["area_cac_result"],
                "selection": self.sT["geometry"]["selection"],
            },
            "mesh": self.sT["mesh"],
            "materials": self.sT["materials"],
            "boundaries": self.sT["boundaries"],
            "physics_entities": self.sT["physics_entities"],
            "diagnostic": self.sT["diagnostic"],
            "global": self.sT["global_settings"],
        }
        
    def _first_item(self, d):
        """安全获取 dict 的第一个 (key, value)，空 dict 返回 None"""
        return str(next(iter(d.items()), None))

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
        

# 测试代码
if __name__ == "__main__":
    pass
