"""
==========================
src/domain/config/m2u_convconst.py
==========================
定义转换系统运行所需的动态常量，并从 JSON 读取可编辑默认值。
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

from pint import UnitRegistry

from src.domain.utils.get_geom_num import geo_counter


def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while not (current / ".project_mark").exists():
        if current.parent == current:
            raise FileNotFoundError("未找到项目根目录，请检查 .project_mark 文件")
        current = current.parent
    return current


project_root = _find_project_root()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

ureg = UnitRegistry()

DEFAULTS_PATH = project_root / "src" / "infrastructure" / "m2u_convconst_defaults.json"
LEGACY_DEFAULTS_PATH = Path(__file__).with_name("m2u_convconst_defaults.json")
FALLBACK_DEFAULTS: dict[str, Any] = {
    "runtime_defaults": {
        "bool_Revo_vector": False,
        "IF_Conv2Void": True,
        "axis_mcl_dir": "X",
        "axis_unipic_dir": "Z",
        "ywaveResolutionRatio": 200,
        "zwaveResolutionRatio": 200,
        "unit_lr": "1e-3 meter",
        "emitter_type": "",
        "material_dir": r"D:\UNIPIC\Unipic2.5D_Training\UNIPIC20240819\bin\pic\MyRBWO\Material\material.xml",
    },
    "debug_defaults": {
        "variable_debug": True,
        "function_debug": False,
        "str2qty_debug": False,
        "emit_debug": False,
        "area_debug": False,
        "port_debug": False,
        "conduct2void_debug": True,
        "llmconv_debug": False,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_conv_defaults() -> dict[str, Any]:
    if not DEFAULTS_PATH.exists() and LEGACY_DEFAULTS_PATH.exists():
        DEFAULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULTS_PATH.write_text(LEGACY_DEFAULTS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    if not DEFAULTS_PATH.exists():
        return json.loads(json.dumps(FALLBACK_DEFAULTS))

    loaded = json.loads(DEFAULTS_PATH.read_text(encoding="utf-8"))
    return _deep_merge(FALLBACK_DEFAULTS, loaded)


def save_conv_defaults(data: dict[str, Any]) -> Path:
    merged = _deep_merge(FALLBACK_DEFAULTS, data)
    DEFAULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULTS_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return DEFAULTS_PATH


class ConvConstants:
    def __init__(
        self,
        data_dir_name: str,
        emitter_type: str | None = None,
        material_dir: str | None = None,
        axis_mcl_dir: str | None = None,
        axis_unipic_dir: str | None = None,
    ) -> None:
        defaults = load_conv_defaults()["runtime_defaults"]

        self.PI = math.pi
        self.bool_Revo_vector = bool(defaults["bool_Revo_vector"])
        self.geo_c = geo_counter()
        self.unit_lr = ureg(defaults["unit_lr"])

        self.data_dir = project_root / "data" / data_dir_name
        self.pre_jsonl = self.data_dir / "workdir" / "preprocessed.jsonl"
        self.parsed_json = self.data_dir / "workdir" / "parsed_result.json"

        self.symbols_json = self.data_dir / "workdir" / "varibles.json"
        self.infile_dir = self.data_dir / "Simulation"
        self.uni_symbols_json = self.data_dir / "workdir" / "uni_symbols.json"

        self.mid_symbol1_json = self.data_dir / "workdir" / "mid_round1.json"
        self.mid_symbol2_json = self.data_dir / "workdir" / "mid_round2.json"
        self.mid_symbols_json = self.data_dir / "workdir" / "mid_symbols.json"

        self.llmconv_json = self.data_dir / "workdir" / "llmconv.json"
        self.llm_prompt_txt = self.data_dir / "workdir" / "llm_prompt.txt"
        self.llm_io_dir = self.data_dir / "workdir" / "llm_io_log.txt"

        self.IF_Conv2Void = bool(defaults["IF_Conv2Void"])
        self.axis_mcl_dir = axis_mcl_dir if axis_mcl_dir is not None else str(defaults["axis_mcl_dir"])
        self.axis_unipic_dir = (
            axis_unipic_dir if axis_unipic_dir is not None else str(defaults["axis_unipic_dir"])
        )
        self.ywaveResolutionRatio = defaults["ywaveResolutionRatio"]
        self.zwaveResolutionRatio = defaults["zwaveResolutionRatio"]

        self.positive_port_mask_num = -1
        self.open_port_mask_num = -1
        self.emitter_mask_num = []

        self.emitter_type = emitter_type if emitter_type is not None else str(defaults["emitter_type"])
        self.material_dir = material_dir if material_dir is not None else str(defaults["material_dir"])


constants: ConvConstants | None = None


def init_constants(*args: Any, **kwargs: Any) -> ConvConstants:
    global constants
    constants = ConvConstants(*args, **kwargs)
    return constants


class AllDebug:
    def __init__(self) -> None:
        defaults = load_conv_defaults()["debug_defaults"]
        self.variable_debug = bool(defaults["variable_debug"])
        self.function_debug = bool(defaults["function_debug"])
        self.str2qty_debug = bool(defaults["str2qty_debug"])
        self.emit_debug = bool(defaults["emit_debug"])
        self.area_debug = bool(defaults["area_debug"])
        self.port_debug = bool(defaults["port_debug"])
        self.conduct2void_debug = bool(defaults["conduct2void_debug"])
        self.llmconv_debug = bool(defaults["llmconv_debug"])


alldebug = AllDebug()
