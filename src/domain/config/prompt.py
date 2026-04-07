from __future__ import annotations

from src.domain.config.prompt_loader import load_prompt_config

_PROMPT_CONFIG = load_prompt_config()

m2u_task_dict = _PROMPT_CONFIG["m2u_task_dict"]
parse_cmd_dict = _PROMPT_CONFIG["parse_cmd_dict"]
json_dict = _PROMPT_CONFIG["json_dict"]
mcl2mid_mclcontext_dict = _PROMPT_CONFIG["mcl2mid_mclcontext_dict"]
mcl2mid_midcontext_dict = _PROMPT_CONFIG["mcl2mid_midcontext_dict"]
mcl2mid_json_dict = _PROMPT_CONFIG["mcl2mid_json_dict"]
