from __future__ import annotations

from src.domain.config.prompt_loader import load_prompt_config


def get_prompt_config() -> dict[str, dict[str, str]]:
    return load_prompt_config()


def get_m2u_task_dict() -> dict[str, str]:
    return get_prompt_config()["m2u_task_dict"]


def get_parse_cmd_dict() -> dict[str, str]:
    return get_prompt_config()["parse_cmd_dict"]


def get_json_dict() -> dict[str, str]:
    return get_prompt_config()["json_dict"]


def get_mcl2mid_mclcontext_dict() -> dict[str, str]:
    return get_prompt_config()["mcl2mid_mclcontext_dict"]


def get_mcl2mid_midcontext_dict() -> dict[str, str]:
    return get_prompt_config()["mcl2mid_midcontext_dict"]


def get_mcl2mid_json_dict() -> dict[str, str]:
    return get_prompt_config()["mcl2mid_json_dict"]
