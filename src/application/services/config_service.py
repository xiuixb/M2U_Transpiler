import json
from pathlib import Path
from typing import Any

from src.domain.config.m2u_convconst import init_constants, alldebug
from src.infrastructure.sys_config import SysConfigStore


class ConfigService:
    """
    配置服务：
    1. 系统启动时读取/创建根目录 `sys_config.json`
    2. 选择器件后写入当前器件路径
    3. 自动初始化 `<device_dir>/workdir/m2u_config.json`
    """

    SYSTEM_CONFIG_FILENAME = "sys_config.json"
    DEVICE_CONFIG_FILENAME = "m2u_config.json"

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]
        self.src_root = self.project_root / "src"
        self.sys_store = SysConfigStore(self.src_root)
        self.system_config_path = self.sys_store.path

    def initialize(self) -> dict[str, Any]:
        config = self.load_system_config()
        current_input = config.get("current_input_file")
        device_state = None
        if current_input:
            input_path = Path(current_input)
            if input_path.exists():
                device_state = self.select_device(str(input_path), persist=False)
            else:
                config["current_input_file"] = ""
                self.save_system_config(config)
        return {
            "system_config_path": str(self.system_config_path),
            "system_config": config,
            "device_state": device_state,
        }

    def load_system_config(self) -> dict[str, Any]:
        return self.sys_store.load()

    def save_system_config(self, config_data: dict[str, Any]) -> Path:
        return self.sys_store.save(config_data)

    def select_device(self, input_file: str, persist: bool = True) -> dict[str, Any]:
        input_path = Path(input_file).resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"器件文件不存在: {input_path}")

        device_dir = input_path.parent
        workdir = device_dir / "workdir"
        workdir.mkdir(parents=True, exist_ok=True)

        device_name = device_dir.name
        device_config_path = workdir / self.DEVICE_CONFIG_FILENAME
        device_config = self.load_device_config(str(input_path))

        if persist:
            self.sys_store.set_current_input_file(str(input_path), device_name)

        return {
            "device_name": device_name,
            "input_file": str(input_path),
            "device_dir": str(device_dir),
            "workdir": str(workdir),
            "device_config_path": str(device_config_path),
            "device_config": device_config,
        }

    def load_device_config(self, input_file: str) -> dict[str, Any]:
        input_path = Path(input_file).resolve()
        device_name = input_path.parent.name
        constants = init_constants(device_name)
        config_path = self.get_device_config_path(str(input_path))

        default_config = {
            "device_name": device_name,
            "input_file": str(input_path),
            "paths": {
                "data_dir": str(constants.data_dir),
                "workdir": str(constants.pre_jsonl.parent),
                "pre_jsonl": str(constants.pre_jsonl),
                "parsed_json": str(constants.parsed_json),
                "mid_symbol1_json": str(constants.mid_symbol1_json),
                "mid_symbol2_json": str(constants.mid_symbol2_json),
                "mid_symbols_json": str(constants.mid_symbols_json),
                "uni_symbols_json": str(constants.uni_symbols_json),
                "llmconv_json": str(constants.llmconv_json),
                "llm_prompt_txt": str(constants.llm_prompt_txt),
                "llm_io_dir": str(constants.llm_io_dir),
                "symbols_json": str(constants.symbols_json),
                "infile_dir": str(constants.infile_dir),
                "material_dir": str(constants.material_dir),
            },
            "runtime": {
                "axis_mcl_dir": constants.axis_mcl_dir,
                "axis_unipic_dir": constants.axis_unipic_dir,
                "IF_Conv2Void": constants.IF_Conv2Void,
                "bool_Revo_vector": constants.bool_Revo_vector,
                "ywaveResolutionRatio": constants.ywaveResolutionRatio,
                "zwaveResolutionRatio": constants.zwaveResolutionRatio,
                "unit_lr": str(constants.unit_lr),
                "emitter_type": constants.emitter_type,
            },
            "debug": {
                "variable_debug": alldebug.variable_debug,
                "function_debug": alldebug.function_debug,
                "str2qty_debug": alldebug.str2qty_debug,
                "emit_debug": alldebug.emit_debug,
                "area_debug": alldebug.area_debug,
                "port_debug": alldebug.port_debug,
                "conduct2void_debug": alldebug.conduct2void_debug,
                "llmconv_debug": alldebug.llmconv_debug,
            },
        }

        if not config_path.exists():
            self.save_device_config(str(input_path), default_config)
            return default_config

        return self._deep_merge(default_config, self._read_json(config_path))

    def save_device_config(self, input_file: str, config_data: dict[str, Any]) -> Path:
        config_path = self.get_device_config_path(input_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return config_path

    def get_current_input_file(self) -> str:
        return self.load_system_config().get("current_input_file", "")

    def get_device_config_path(self, input_file: str) -> Path:
        input_path = Path(input_file).resolve()
        return input_path.parent / "workdir" / self.DEVICE_CONFIG_FILENAME

    def _read_json(self, path: Path) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
