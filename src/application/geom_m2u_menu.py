import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if parent_dir != current_dir:
        current_dir = parent_dir
    else:
        raise FileNotFoundError("未找到项目根目录，请检查 .project_mark 文件")
project_root = current_dir
sys.path.append(project_root)


from src.domain.config.symbolBase  import MagicSymbolTable, MidSymbolTable, Unipic25dSymbolTable
from src.domain.config.cmd_dic_loader import CMD_KEYWORDS_MULTI, CMD_KEYWORDS_SINGLE, PreprocessCmd
from src.domain.core.m2u_parser_route import parse_route_cfg
from src.domain.mclparse.parser_classifier import ParserClassifier

from src.domain.mclparse.mcl_llmpreprocess import LLMPreprocess
from src.domain.mclparse.mcl_parseflow import MCLParseFlow

from src.domain.config.m2u_convconst import init_constants, alldebug
from src.domain.core.dependency_retriever import DependencyRetriever
from src.domain.core.geom_cac import GeomCac
from src.domain.mclconv.mcl2midsT_llmconv import MCL2MID_STConv
from src.domain.core.mid2Files import Mid2Files
from src.domain.unigenerate.mid2uni_sTconv import MID2UNI_STConv
from src.domain.mclconv.mid_sTconv import MID_STConv
from src.domain.unigenerate.uni2Files import Uni2Files
from src.domain.unigenerate.uni2inFiles import Uni2InFiles


STEP_LABELS = {
    0: "选择工作文件夹",
    1: "预处理",
    2: "解析",
    3: "符号处理",
    4: "差异转换",
    5: "文件生成",
}


class MAGIC2UNIPIC:
    def __init__(self, input_file: str):
        self.parser_classifier = ParserClassifier(route_config=parse_route_cfg)
        self.preprocessor = LLMPreprocess(rules=PreprocessCmd())
        self.allparser = MCLParseFlow(parser_classifier=self.parser_classifier)
        self.geom_cac = GeomCac()
        self.dependency_retriever = DependencyRetriever()
        self.input_file = ""
        self.input_file_path: Path | None = None
        self.base_name = ""
        self.constants = None
        self.magic_symbols = MagicSymbolTable()
        self.mid_symbols = MidSymbolTable()
        self.uni_symbols = Unipic25dSymbolTable()
        self.mcl2mid_conv = None
        self.mid_conv = None
        self.mid2uni_conv = None
        self.uni2files = Uni2Files()
        self.mid2files = Mid2Files()
        self.uni2infiles = Uni2InFiles()
        self.set_input_file(input_file)

    def set_input_file(self, input_file: str):
        input_path = Path(input_file).resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_path}")

        self.input_file = str(input_path)
        self.input_file_path = input_path
        self.base_name = input_path.parent.name
        self.constants = init_constants(self.base_name)

        self.magic_symbols = MagicSymbolTable()
        self.mid_symbols = MidSymbolTable()
        self.uni_symbols = Unipic25dSymbolTable()
        self.mcl2mid_conv = MCL2MID_STConv(
            magic_symbols=self.magic_symbols,
            mid_symbols=self.mid_symbols,
            dependency_retriever=self.dependency_retriever,
        )
        self.mid_conv = MID_STConv(mid_symbols=self.mid_symbols, geom_conv=self.geom_cac)
        self.mid2uni_conv = MID2UNI_STConv(
            mid_symbols=self.mid_symbols,
            uni_symbols=self.uni_symbols,
            geo_c=self.constants.geo_c,
        )

    def ensure_workdir(self):
        self.constants.pre_jsonl.parent.mkdir(parents=True, exist_ok=True)

    def _require_file(self, path: Path, step_name: str):
        if not path.exists():
            raise FileNotFoundError(f"{step_name} 需要的中间产物不存在: {path}")

    def _read_json(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _read_jsonl(self, path: Path):
        items = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items

    def _write_json(self, path: Path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_jsonl(self, path: Path, items):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def _load_mid_symbols(self, path: Path):
        self._require_file(path, "读取 Mid Symbol")
        mid_symbols = MidSymbolTable()
        mid_symbols.sT = self._read_json(path)
        self.mid_symbols = mid_symbols
        return mid_symbols

    def _load_uni_symbols(self, path: Path):
        self._require_file(path, "读取 UNI Symbol")
        data = self._read_json(path)
        uni_symbols = Unipic25dSymbolTable()
        for key, value in data.items():
            setattr(uni_symbols, key, value)
        self.uni_symbols = uni_symbols
        return uni_symbols

    def print_context(self):
        print("\n当前工作上下文")
        print(f"  器件: {self.base_name}")
        print(f"  输入文件: {self.input_file}")
        print(f"  workdir: {self.constants.pre_jsonl.parent}")

    def step_preprocess(self):
        self.ensure_workdir()
        print("\n=====> Step 1: 预处理")
        start = time.time()
        with open(self.input_file, "r", encoding="utf-8", errors="replace") as f:
            input_str = f.read()

        lines = input_str.splitlines(keepends=False)
        pre_items = self.preprocessor.mcl_preprocess(lines)
        self._write_jsonl(self.constants.pre_jsonl, pre_items)

        print(f"预处理完成: {self.constants.pre_jsonl}")
        print(f"耗时: {time.time() - start:.2f}s")
        return pre_items

    def step_parse(self):
        print("\n=====> Step 2: 解析")
        start = time.time()
        pre_items = self._read_jsonl(self.constants.pre_jsonl)
        filtered_items = [
            item
            for item in pre_items
            if not (item.get("para", {}).get("ignore") == "yes")
        ]
        parsed_dicts = self.allparser.mclparser_in_memory(filtered_items)
        self._write_json(self.constants.parsed_json, parsed_dicts)

        print(f"解析完成: {self.constants.parsed_json}")
        print(f"耗时: {time.time() - start:.2f}s")
        return parsed_dicts

    def step_convert_round1(self):
        print("\n=====> Step 3: 一轮转换")
        start = time.time()
        parsed_dicts = self._read_json(self.constants.parsed_json)

        self.mcl2mid_conv.load_list(
            parsed_dicts=parsed_dicts,
            unit_lr=self.constants.unit_lr,
            axis_mcl_dir=self.constants.axis_mcl_dir,
            geo_c=self.constants.geo_c,
            llm_io_dir=self.constants.llm_io_dir,
            area_debug=alldebug.area_debug,
            variable_debug=alldebug.variable_debug,
            function_debug=alldebug.function_debug,
            port_debug=alldebug.port_debug,
            llmconv_debug=alldebug.llmconv_debug,
        )
        self.magic_symbols, self.mid_symbols, llmconv_list = self.mcl2mid_conv.mcl2mid_sTconv()

        self._write_json(self.constants.mid_symbol1_json, self.mid_symbols.to_dict())
        self._write_json(self.constants.llmconv_json, llmconv_list)

        self.constants.llm_prompt_txt.parent.mkdir(parents=True, exist_ok=True)
        with open(self.constants.llm_prompt_txt, "w", encoding="utf-8") as f:
            for test_item in self.mid_symbols.sT.get("test", []):
                f.write(test_item.get("txt", "") + "\n\n\n\n")

        print(f"一轮转换完成: {self.constants.mid_symbol1_json}")
        print(f"LLM 转换记录: {self.constants.llmconv_json}")
        print(f"耗时: {time.time() - start:.2f}s")
        return self.mid_symbols

    def step_convert_round2(self):
        print("\n=====> Step 4: 二轮转换")
        start = time.time()
        self.mid_symbols = self._load_mid_symbols(self.constants.mid_symbol1_json)
        self.mid_conv.load_data(self.mid_symbols)
        self.mid_symbols = self.mid_conv.mid_sTconv(
            IF_Conv2Void=self.constants.IF_Conv2Void,
            conduct2void_debug=alldebug.conduct2void_debug,
            emit_debug=alldebug.emit_debug,
        )
        self._write_json(self.constants.mid_symbol2_json, self.mid_symbols.to_dict())

        print(f"二轮转换完成: {self.constants.mid_symbol2_json}")
        print(f"耗时: {time.time() - start:.2f}s")
        return self.mid_symbols

    def step_convert_round3_and_generate(self):
        print("\n=====> Step 5: 三轮转换+生成")
        start = time.time()
        self.mid_symbols = self._load_mid_symbols(self.constants.mid_symbol2_json)

        self.mid2uni_conv.load_data(self.mid_symbols)
        self.uni_symbols = self.mid2uni_conv.mid2uni_sTconv(
            symbols_file=str(self.constants.symbols_json),
            unit_lr=self.constants.unit_lr,
            axis_mcl_dir=self.constants.axis_mcl_dir,
            geo_c=self.constants.geo_c,
            ywaveResolutionRatio=self.constants.ywaveResolutionRatio,
            zwaveResolutionRatio=self.constants.zwaveResolutionRatio,
            IF_Conv2Void=self.constants.IF_Conv2Void,
            bool_Revo_vector=self.constants.bool_Revo_vector,
            material_dir=self.constants.material_dir,
        )

        self.mid2files.load_data(self.mid_symbols)
        self.mid2files.save_data_to_json(str(self.constants.mid_symbols_json))

        self.uni2files.load_data(self.uni_symbols)
        self.uni2files.save_data_to_json(str(self.constants.uni_symbols_json))

        self.uni2infiles.load_data(self.uni_symbols, self.constants.infile_dir)
        self.uni2infiles.write_all()

        print(f"Mid symbols: {self.constants.mid_symbols_json}")
        print(f"Uni symbols: {self.constants.uni_symbols_json}")
        print(f"输出目录: {self.constants.infile_dir}")
        print(f"耗时: {time.time() - start:.2f}s")
        return self.uni_symbols

    def run_step(self, step: int):
        if step == 1:
            return self.step_preprocess()
        if step == 2:
            return self.step_parse()
        if step == 3:
            return self.step_convert_round1()
        if step == 4:
            return self.step_convert_round2()
        if step == 5:
            return self.step_convert_round3_and_generate()
        raise ValueError(f"不支持的步骤: {step}")

    def m2u_pipeline(self):
        start = time.time()
        self.step_preprocess()
        self.step_parse()
        self.step_convert_round1()
        self.step_convert_round2()
        self.step_convert_round3_and_generate()
        print("\n=================================")
        print("Pipeline completed.")
        print(f"Preprocess:     {self.constants.pre_jsonl}")
        print(f"Parse:          {self.constants.parsed_json}")
        print(f"Conv round 1:   {self.constants.mid_symbol1_json}")
        print(f"Conv round 2:   {self.constants.mid_symbol2_json}")
        print(f"Conv round 3:   {self.constants.uni_symbols_json}")
        print(f"Total time: {time.time() - start:.2f}s")


def find_input_file(work_dir: Path):
    candidates = sorted(work_dir.glob("*.m2d"))
    if not candidates:
        candidates = sorted(work_dir.glob("*.mcl"))
    if not candidates:
        raise FileNotFoundError(f"未在目录中找到 .m2d 或 .mcl 文件: {work_dir}")
    return candidates[0]


def list_device_dirs():
    data_dir = Path(project_root) / "data"
    return sorted(
        path for path in data_dir.iterdir()
        if path.is_dir() and any(path.glob("*.m2d"))
    )


def choose_work_dir():
    device_dirs = list_device_dirs()
    if not device_dirs:
        raise FileNotFoundError("data 目录下未找到包含 .m2d 文件的器件目录")

    print("\n可选工作文件夹")
    for idx, folder in enumerate(device_dirs, start=1):
        print(f"  {idx}. {folder.name}")

    while True:
        raw = input("请选择工作文件夹编号: ").strip()
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(device_dirs):
                return device_dirs[index - 1]
        print("输入无效，请重新输入。")


def print_menu(m2u: MAGIC2UNIPIC):
    m2u.print_context()
    print("\n菜单")
    print("  0. 选择工作文件夹")
    print("  1. 预处理")
    print("  2. 解析")
    print("  3. 一轮转换")
    print("  4. 二轮转换")
    print("  5. 三轮转换+生成")
    print("  9. 整体流水线")
    print("  q. 退出")


def wait_back_to_menu():
    input("\n按回车返回菜单...")


def run_step_in_terminal(input_file: str, step: str):
    cmd = [
        sys.executable,
        "-u",
        str(Path(__file__).resolve()),
        "-I",
        input_file,
        "-S",
        step,
    ]
    subprocess.run(cmd, check=False)


def interactive_menu(initial_input_file: str | None = None):
    if initial_input_file:
        m2u = MAGIC2UNIPIC(initial_input_file)
    else:
        work_dir = choose_work_dir()
        m2u = MAGIC2UNIPIC(str(find_input_file(work_dir)))

    while True:
        print_menu(m2u)
        choice = input("请选择菜单项: ").strip().lower()

        try:
            if choice == "q":
                print("已退出。")
                return
            if choice == "0":
                work_dir = choose_work_dir()
                m2u.set_input_file(str(find_input_file(work_dir)))
                print(f"已切换到: {work_dir}")
                wait_back_to_menu()
                continue
            if choice == "9":
                run_step_in_terminal(m2u.input_file, choice)
                wait_back_to_menu()
                continue
            if choice in {"1", "2", "3", "4", "5"}:
                run_step_in_terminal(m2u.input_file, choice)
                wait_back_to_menu()
                continue
            print("输入无效，请重新选择。")
        except Exception as exc:
            print(f"[ERROR] {exc}")
            wait_back_to_menu()


def main():
    parser = argparse.ArgumentParser(description="几何流程菜单版 MAGIC2UNIPIC")
    parser.add_argument("-I", "--input_file", type=str, help="输入文件路径")
    parser.add_argument(
        "-S",
        "--step",
        type=int,
        choices=[1, 2, 3, 4, 5, 9],
        help="直接执行指定步骤，9 表示执行整体流水线",
    )
    parser.add_argument("--menu", action="store_true", help="强制进入交互菜单")
    args = parser.parse_args()

    if args.menu or args.step is None:
        interactive_menu(args.input_file)
        return

    if not args.input_file:
        raise ValueError("非菜单模式下必须提供 -I/--input_file")

    m2u = MAGIC2UNIPIC(args.input_file)
    if args.step == 9:
        m2u.m2u_pipeline()
    else:
        m2u.run_step(args.step)


if __name__ == "__main__":
    main()
