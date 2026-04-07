import json
from pathlib import Path
from typing import Any

from src.domain.config.cmd_dic_loader import MCLParse_CmdDict
from src.domain.config.llm_route_config_loader import get_llm_route_config_path
from src.domain.config.m2u_convconst import (
    init_constants,
    load_conv_defaults,
    save_conv_defaults,
)
from src.domain.config.prompt_loader import get_prompt_config_path, load_prompt_config, save_prompt_config
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
    ROUTE_CONFIG_FILENAME = "llm_route_config.json"

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]
        self.infra_root = self.project_root / "src" / "infrastructure"
        self.sys_store = SysConfigStore(self.infra_root)
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

    def load_conv_defaults(self) -> dict[str, Any]:
        return load_conv_defaults()

    def save_conv_defaults(self, conv_defaults: dict[str, Any]) -> Path:
        return save_conv_defaults(conv_defaults)

    def load_prompt_config(self) -> dict[str, dict[str, str]]:
        return load_prompt_config()

    def save_prompt_config(self, prompt_config: dict[str, dict[str, str]]) -> Path:
        return save_prompt_config(prompt_config)

    def get_prompt_config_path(self) -> Path:
        return get_prompt_config_path()

    def get_route_config_path(self) -> Path:
        return get_llm_route_config_path()

    def load_route_config(self) -> dict[str, Any]:
        route_path = self.get_route_config_path()
        route_data = json.loads(route_path.read_text(encoding="utf-8"))

        supported_commands = sorted(MCLParse_CmdDict().MCL2Kind.keys())
        regex_commands = set(route_data.get("regexparse_commands", []))
        llm_commands = set(route_data.get("llmparse_commands", []))
        llmconv_commands = set(route_data.get("mcl2mid_llmconv_commands", []))

        rows = []
        for command in supported_commands:
            rows.append(
                {
                    "command": command,
                    "pure_rule": command not in llm_commands,
                    "llm_parse": command in llm_commands,
                    "llm_symbol": command in llmconv_commands,
                }
            )

        return {
            "path": str(route_path),
            "supported_commands": supported_commands,
            "multiword_prefixes": sorted(route_data.get("multiword_prefixes", [])),
            "regexparse_commands": sorted(regex_commands),
            "llmparse_commands": sorted(llm_commands),
            "llmparse_prefixes": sorted(route_data.get("llmparse_prefixes", [])),
            "llmparse_patterns": list(route_data.get("llmparse_patterns", [])),
            "mcl2mid_llmconv_commands": sorted(llmconv_commands),
            "command_rows": rows,
        }

    def save_route_config(self, route_config: dict[str, Any]) -> Path:
        route_path = self.get_route_config_path()
        data = {
            "multiword_prefixes": sorted(route_config.get("multiword_prefixes", [])),
            "regexparse_commands": sorted(route_config.get("regexparse_commands", [])),
            "llmparse_commands": sorted(route_config.get("llmparse_commands", [])),
            "llmparse_prefixes": sorted(route_config.get("llmparse_prefixes", [])),
            "llmparse_patterns": list(route_config.get("llmparse_patterns", [])),
            "mcl2mid_llmconv_commands": sorted(route_config.get("mcl2mid_llmconv_commands", [])),
        }
        route_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return route_path

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
                "mid_round1_json": str(constants.mid_symbol1_json),
                "mid_round2_json": str(constants.mid_symbol2_json),
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
            "geometry_preview": {
                "aspect_ratio": 1.0,
                "resolution_scale": 1.0,
            },
        }

        if not config_path.exists():
            self.save_device_config(str(input_path), default_config)
            return default_config

        merged = self._deep_merge(default_config, self._read_json(config_path))
        merged.pop("debug", None)
        return merged

    def save_device_config(self, input_file: str, config_data: dict[str, Any]) -> Path:
        config_path = self.get_device_config_path(input_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(config_data)
        data.pop("debug", None)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
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
