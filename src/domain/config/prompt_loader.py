from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any


PROMPT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "infrastructure" / "prompt_config.json"
LEGACY_PROMPT_PATH = Path(__file__).resolve().with_name("prompt.py")


def get_prompt_config_path() -> Path:
    return PROMPT_CONFIG_PATH


def _normalize_prompt_text(value: str) -> str:
    normalized = textwrap.dedent(value).strip("\n")
    return normalized


def _normalize_prompt_config(data: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        group: {
            key: _normalize_prompt_text(str(value))
            for key, value in entries.items()
        }
        for group, entries in data.items()
    }


def load_prompt_config() -> dict[str, dict[str, str]]:
    path = get_prompt_config_path()
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    data = {group: dict(entries) for group, entries in raw.items()}
    return _normalize_prompt_config(data)


def save_prompt_config(data: dict[str, dict[str, str]]) -> Path:
    path = get_prompt_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_prompt_config(data)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
