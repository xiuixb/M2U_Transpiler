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

from src.domain.config.symbolBase import MidSymbolTable

class Mid2Files:
    def load_data(self, mid_symbols: MidSymbolTable):
        self.mid_symbols = mid_symbols
        
    def save_data_to_json(self, mid_symbols_file_path: str):

        with open(mid_symbols_file_path, "w", encoding="utf-8") as f:
            json.dump(self.mid_symbols.to_dict(), f, ensure_ascii=False, indent=2)
