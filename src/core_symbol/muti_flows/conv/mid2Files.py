import os
import sys
import json

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from src.core_symbol.symbolBase import MidSymbolTable

class Mid2Files:
    def load_data(self, mid_symbols: MidSymbolTable):
        self.mid_symbols = mid_symbols
        
    def save_data_to_json(self, mid_symbols_file_path: str):

        with open(mid_symbols_file_path, "w", encoding="utf-8") as f:
            mid_symbols_json = {
                "symbol_table": self.mid_symbols.symbol_table,
                "functions": self.mid_symbols.functions,
                "geom": self.mid_symbols.geom,
                "grid": self.mid_symbols.grid,
                "ports": self.mid_symbols.ports,
                "emits": self.mid_symbols.emits,
                "observes": self.mid_symbols.observes,
                "presets": self.mid_symbols.presets,
                "freespace": self.mid_symbols.freespace,
                "inductor": self.mid_symbols.inductor,
                "FieldsDgn": self.mid_symbols.FieldsDgn,
                "timers": self.mid_symbols.timers,
                "area_entities": self.mid_symbols.area_entities,
                "void_area": self.mid_symbols.void_area,
                "geom_other_entity": self.mid_symbols.geom_other_entity,
                "result": self.mid_symbols.result,
            }
                            
            json.dump(mid_symbols_json, f, ensure_ascii=False, indent=2)
