from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class LLMRouteConfigData:
    multiword_prefixes: set[str]
    regexparse_commands: set[str]
    llmparse_commands: set[str]
    llmparse_prefixes: set[str]
    llmparse_patterns: list[str]
    mcl2mid_llmconv_commands: tuple[str, ...]


def get_llm_route_config_path() -> Path:
    path = Path(__file__).resolve().parents[2] / "infrastructure" / "llm_route_config.json"
    legacy_path = Path(__file__).resolve().with_name("llm_route_config.json")
    if not path.exists() and legacy_path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(legacy_path.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def load_llm_route_config() -> LLMRouteConfigData:
    path = get_llm_route_config_path()
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return LLMRouteConfigData(
        multiword_prefixes=set(raw.get("multiword_prefixes", [])),
        regexparse_commands=set(raw.get("regexparse_commands", [])),
        llmparse_commands=set(raw.get("llmparse_commands", [])),
        llmparse_prefixes=set(raw.get("llmparse_prefixes", [])),
        llmparse_patterns=list(raw.get("llmparse_patterns", [])),
        mcl2mid_llmconv_commands=tuple(raw.get("mcl2mid_llmconv_commands", [])),
    )
