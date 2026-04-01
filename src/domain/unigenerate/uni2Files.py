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

from src.domain.config.symbolBase import Unipic25dSymbolTable

class Uni2Files:
    def load_data(self, uni_symbols: Unipic25dSymbolTable):
        self.uni_symbols = uni_symbols
        
    def save_data_to_json(self, uni_symbols_file_path: str):
        with open(uni_symbols_file_path, "w", encoding="utf-8") as f:
            uni_symbols_json = {
                "buildIn": self.uni_symbols.buildIn,
                "FaceBndIn": self.uni_symbols.FaceBndIn,
                "PtclSourcesIn": self.uni_symbols.PtclSourcesIn,
                "SpeciesIn": self.uni_symbols.SpeciesIn,
                "PMLIn": self.uni_symbols.PMLIn,
                "StaticNodeFLdsIn": self.uni_symbols.StaticNodeFLdsIn,
                "CircuitModelIn": self.uni_symbols.CircuitModelIn,
                "GlobalSettingIn": self.uni_symbols.GlobalSettingIn,
                "FieldsDgnIn": self.uni_symbols.FieldsDgnIn,
            }
            json.dump(uni_symbols_json, f, ensure_ascii=False, indent=2)
