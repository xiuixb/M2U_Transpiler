from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_data() -> dict[str, Any]:
    path = Path(__file__).resolve().with_name("cmd_dic.json")
    return json.loads(path.read_text(encoding="utf-8"))


class MCLParse_CmdDict:
    def __init__(self):
        data = _load_data()["mcl_parse_cmd_dict"]
        self.MCL2Kind = data["MCL2Kind"]


class MCL2MID_CmdDict:
    def __init__(self):
        data = _load_data()["mcl2mid_cmd_dict"]
        self.MCL_dependency_dict = data["MCL_dependency_dict"]
        self.MID_dict = data["MID_dict"]
        self.MCL2MID_llmconv_List = data["MCL2MID_llmconv_List"]
        self.MID_dependency_dict = data["MID_dependency_dict"]


class PreprocessCmd:
    _data = _load_data()["preprocess_cmd"]
    commands_to_skip = _data["commands_to_skip"]
    commands_to_skip_byOptions = _data["commands_to_skip_byOptions"]
    options_to_skip = _data["options_to_skip"]
    options_of_command = _data["options_of_command"]
    float_e_exp = _data["float_e_exp"]
    float_exp = _data["float_exp"]
    float_ext_exp = _data["float_ext_exp"]
    identity_exp = _data["identity_exp"]


CMD_KEYWORDS_SINGLE = set(_load_data()["cmd_keywords_single"])
CMD_KEYWORDS_MULTI = set(_load_data()["cmd_keywords_multi"])
