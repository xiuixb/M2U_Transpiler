from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AppState:
    current_device: dict[str, Any] | None = None
    device_config: dict[str, Any] | None = None
    route_config: dict[str, Any] | None = None
    conv_defaults: dict[str, Any] | None = None
    prompt_config: dict[str, dict[str, str]] | None = None
    mode: str = "llm"
    is_running: bool = False
    active_panel: str = "device"
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    opened_artifact: dict[str, Any] | None = None
    artifact_content: str = ""
    simulation_files: list[dict[str, Any]] = field(default_factory=list)
    opened_simulation_file: dict[str, Any] | None = None
    simulation_content: str = ""
    geometry_area_result: dict[str, Any] | None = None
    geometry_source_path: str = ""
    geometry_preview_path: str = ""
    geometry_preview_kind: str = "pec"
    geometry_aspect_ratio: float = 1.0
    geometry_resolution_scale: float = 1.0
    pointset_path: str = ""
    pointset_rows: list[list[str]] = field(default_factory=list)
    config_dirty: bool = False
    route_dirty: bool = False
    conv_defaults_dirty: bool = False
    prompt_dirty: bool = False
    artifact_dirty: bool = False
    simulation_dirty: bool = False
    last_run_result: dict[str, Any] | None = None
    message: str = ""
    error_message: str = ""

    @property
    def has_device(self) -> bool:
        return self.current_device is not None

    @property
    def has_config(self) -> bool:
        return self.device_config is not None

    @property
    def can_run(self) -> bool:
        return self.has_device and self.has_config and (not self.is_running)

    @property
    def status_label(self) -> str:
        if self.is_running:
            return "运行中"
        if not self.has_device:
            return "未选择器件"
        if not self.has_config:
            return "已加载器件"
        return "可执行"

    def snapshot(self) -> dict[str, Any]:
        data = asdict(self)
        data["has_device"] = self.has_device
        data["has_config"] = self.has_config
        data["can_run"] = self.can_run
        data["status_label"] = self.status_label
        return data
