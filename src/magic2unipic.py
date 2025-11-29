import os
import sys
import time
import argparse
import json
from pathlib import Path

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from core.symbolBase import *
from core.rules import PreprocessRules, RouteRule

from core.muti_flows.mclparser.parser_route import ParserRoute
from core.muti_flows.mcl_preprocess import MCLPreprocess
from core.muti_flows.mcl_allparser import MCLAllParser
from src.sys_config.route_config import Route_cfg
from src.sys_config.config import init_constants, alldebug
from core.muti_flows.conv.geom_conv import GeomConv
from core.muti_flows.conv.mcl2mid_sTconv import MCL2MID_STConv
from core.muti_flows.conv.mid_sTconv import MID_STConv
from core.muti_flows.conv.mid2uni_sTconv import MID2UNI_STConv
from core.muti_flows.conv.uni2Files import Uni2Files
from core.muti_flows.conv.mid2Files import Mid2Files

class MAGIC2UNIPIC:
    def __init__(self,
                 input_file: str
                 ):
        self.input_file = input_file
        self.parser_route = ParserRoute(config=Route_cfg)
        self.preprocessor = MCLPreprocess(rules=PreprocessRules())
        self.allparser = MCLAllParser(parser_route=self.parser_route)
        self.input_file = input_file
        
        self.input_file_path = Path(input_file)
        self.base_name = self.input_file_path.stem        
        self.constants = init_constants(self.base_name)
        self.geom_conv = GeomConv()
        self.magic_symbols = MagicSymbolTable()
        self.mid_symbols = MidSymbolTable()
        self.uni_symbols = Unipic25dSymbolTable()

        self.mcl2mid_conv = MCL2MID_STConv(magic_symbols=self.magic_symbols, mid_symbols=self.mid_symbols)
        self.mid_conv = MID_STConv(mid_symbols=self.mid_symbols, geom_conv=self.geom_conv)
        self.mid2uni_conv = MID2UNI_STConv(mid_symbols=self.mid_symbols, uni_symbols=self.uni_symbols,geo_c=self.constants.geo_c)
        self.uni2files = Uni2Files()
        self.mid2files = Mid2Files()



    def m2u_pipeline(self, workdir: str = "workdir"):
        """
        读取 input_file -> 分流 -> 写入一个 JSON 文件（包含三组）
        返回分流后的 dict（同 route_items）
        """
        input_file = self.input_file
        start_time = time.time()
        p = self.input_file_path
        constants = self.constants
        out_dir = p.parent / workdir
        out_dir.mkdir(exist_ok=True)        

        # --- Step 1 ---
        print("=====> Step 1: Preprocessing")
        with open(input_file, "r") as f:
            input_str = f.read()

        lines = input_str.splitlines(keepends=False)
        pre_items = self.preprocessor.mcl_preprocess(lines)
        
        with open(constants.pre_jsonl, "w", encoding="utf-8") as fj:
            for it in pre_items:
                fj.write(json.dumps(it, ensure_ascii=False) + "\n")

        # --- Step 2 ---
        print("=====> Step 2: Parsing")
        parsed_dicts = self.allparser.mclparser_in_memory(pre_items)
        
        with open(constants.parsed_json, "w", encoding="utf-8") as fp:
            json.dump(parsed_dicts, fp, ensure_ascii=False, indent=2)


        # --- Step 3 ---
        print("=====> Step 3: Converting to UNI")
        
        self.mcl2mid_conv.load_list(
            parsed_dicts=parsed_dicts, 
            unit_lr=constants.unit_lr,
            axis_mcl_dir=constants.axis_mcl_dir,
            geo_c=constants.geo_c,
            area_debug=alldebug.area_debug,
            variable_debug=alldebug.variable_debug,
            function_debug=alldebug.function_debug,
            port_debug=alldebug.port_debug,
            )
        time_mcl2mid = time.time()
        self.mid_symbols = self.mcl2mid_conv.mcl2mid_sTconv()

        
        time_mid_conv = time.time()
        self.mid_conv.load_data(self.mid_symbols)
        
        self.mid_symbols = self.mid_conv.mid_sTconv(
            IF_Conv2Void=constants.IF_Conv2Void,
            conduct2void_debug=alldebug.conduct2void_debug,
            emit_debug=alldebug.emit_debug
        )

        
        
        time_mid2uni = time.time()
        self.mid2uni_conv.load_data(self.mid_symbols)
        self.uni_symbols = self.mid2uni_conv.mid2uni_sTconv(
            symbols_file=str(constants.symbols_json),
            buildIn_file=str(constants.build_in_dir),
            unit_lr=constants.unit_lr,
            axis_mcl_dir=constants.axis_mcl_dir,
            geo_c=constants.geo_c,
            ywaveResolutionRatio=constants.ywaveResolutionRatio,
            zwaveResolutionRatio=constants.zwaveResolutionRatio,
            IF_Conv2Void=constants.IF_Conv2Void,
            bool_Revo_vector=constants.bool_Revo_vector,
            material_dir=constants.material_dir,
        )

        # --- Step 4 ---
        print("=====> Step 4: Outputting files")
        self.mid2files.load_data(self.mid_symbols)
        self.mid2files.save_data_to_json(str(constants.mid_symbols_json))
        print(f"Mid symbols: {constants.mid_symbols_json}")

        self.uni2files.load_data(self.uni_symbols)
        self.uni2files.save_data_to_json(str(constants.uni_symbols_json))
        print(f"Uni symbols: {constants.uni_symbols_json}")

        # --- Done ---
        print("\n\n=================================")
        print("✅ Pipeline completed.")
        print(f"Preprocess: {constants.pre_jsonl}")
        print(f"Parse:      {constants.parsed_json}")
        print(f"Total Time: {time.time() - start_time:.2f}s")
        print(f"Preprocess time: {time_mcl2mid - start_time:.2f}s")
        print(f"Parse time:      {time_mid_conv - time_mcl2mid:.2f}s")
        print(f"Conv time:       {time_mid2uni - time_mid_conv:.2f}s")
        print(f"Save time:       {time.time() - time_mid_conv:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MAGIC2UNIPIC Pipeline")
    parser.add_argument("input_file", type=str, help="Path to the input file")
    parser.add_argument("--workdir", type=str, default="workdir", help="Path to the work directory")
    args = parser.parse_args()

    m2u = MAGIC2UNIPIC(input_file=args.input_file)
    m2u.m2u_pipeline(args.workdir)