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

from core.symbolBase import MidSymbolTable
from core.muti_flows.conv.geom_conv import GeomConv

class MID_STConv:
    def __init__(self,
                mid_symbols: MidSymbolTable,
                geom_conv: GeomConv
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
        print("[info] 转换器二轮处理……")
        try:
            if IF_Conv2Void:
                print("[info] 区域转换:金属转真空")
                self.mid_symbols.void_area, self.mid_symbols.geom_other_entity = self.geom_conv.conduct2void_utils(area_entities=self.mid_symbols.geom["areas"], conduct2void_debug=conduct2void_debug)
            print("[info] 计算发射参考点")
            self.mid_symbols.void_area, self.mid_symbols.result = self.geom_conv.get_emits_refPnts(self.mid_symbols.emits, self.mid_symbols.geom, self.mid_symbols.void_area, emit_debug)
        except Exception as e:
            print(f"[error] 二轮处理异常: {e}")
            traceback.print_exc()
            raise

        return self.mid_symbols