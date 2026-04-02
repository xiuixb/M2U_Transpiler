import json
from pathlib import Path
from typing import Any


class SysConfigStore:
    """
    系统配置存储。

    负责：
    - 读取/创建 `src/sys_config.json`
    - 保存当前器件路径，供系统启动恢复
    """

    FILENAME = "sys_config.json"

    def __init__(self, src_root: Path | None = None):
        self.src_root = src_root or Path(__file__).resolve().parents[1]
        self.path = self.src_root / self.FILENAME

    def load(self) -> dict[str, Any]:
        default_config = {
            "current_input_file": "",
            "last_device_name": "",
        }
        if not self.path.exists():
            self.save(default_config)
            return default_config
        return self._deep_merge(default_config, self._read_json(self.path))

    def save(self, config_data: dict[str, Any]) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return self.path

    def get_current_input_file(self) -> str:
        return self.load().get("current_input_file", "")

    def set_current_input_file(self, input_file: str, device_name: str = "") -> Path:
        config = self.load()
        config["current_input_file"] = input_file
        config["last_device_name"] = device_name
        return self.save(config)

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
