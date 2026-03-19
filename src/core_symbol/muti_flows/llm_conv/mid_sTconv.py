import os
import sys
import traceback

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from src.core_symbol.symbolBase import MidSymbolTable
from src.core_cac.geom_cac import GeomCac

class MID_STConv:
    def __init__(self,
                mid_symbols: MidSymbolTable,
                geom_conv: GeomCac
                ):
        self.mid_symbols = mid_symbols
        self.geom_conv = geom_conv

    def load_data(self, mid_symbols: MidSymbolTable):
        self.mid_symbols = mid_symbols

    def mid_sTconv(self,
                       IF_Conv2Void: bool = False,
                       conduct2void_debug: bool = False,
                       emit_debug: bool = False
                       ):
        
        ## 处理area实体的基本参数
        area_entities = self.get_area_entities(
            areas=self.mid_symbols.sT["geometry"]["area"],
            material_assigns=self.mid_symbols.sT["materials"]["material_assign"]
        )


        ## 金属转真空
        if IF_Conv2Void:
            print("[info] 区域转换:金属转真空")
            self.mid_symbols.sT["geometry"]["area_cac_result"]["void_area"], self.mid_symbols.sT["geometry"]["area_cac_result"]["other_entity"] = self.geom_conv.conduct2void_utils(
                area_entities=area_entities,
                conduct2void_debug=conduct2void_debug
            )



        emit_apply_idx = None
        for emit_idx, emit in enumerate(self.mid_symbols.sT["physics_entities"]["emit_apply"]):
            if emit["sys_type"] == "emit_apply":
                emit_apply_idx = emit_idx
                break

        if self.mid_symbols.sT["physics_entities"]["emit_apply"]:
            print("[info] 发射参考点计算")
            self.mid_symbols.sT["geometry"]["area_cac_result"]["void_area"], self.mid_symbols.sT["physics_entities"]["emit_apply"][emit_apply_idx]["cac_result"] = self.geom_conv.get_emits_refPnts(
                self.mid_symbols.sT["physics_entities"]["emit_apply"],
                area_entities,
                self.mid_symbols.sT["geometry"]["area_cac_result"]["void_area"],
                emit_debug
            )


        return self.mid_symbols
    
    def get_area_entities(self,
                          areas: dict,
                          material_assigns: list
                          ):
        """
        从中间符号表中构造几何算法需要的area_entities格式(area + material_assign)
        """
        area_entities = {}
        for name, entity in areas.items():
            area_entities[name] = {
                "area_type": entity["area_type"],
                "points": entity["cac_result"]["geom_num"]
            }
        for material_assign in material_assigns:
            geom_name = material_assign["geom_name"]
            mat_name = material_assign["mat_name"]
            area_entities[geom_name]["material"] = mat_name
        return area_entities
    