from __future__ import annotations

import io
import json
import traceback
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtCore import QTimer

from src.application.services import ArtifactService, ConfigService, GeometryPreviewService, PipelineService
from src.presentation.app_state import AppState


class WorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class LogEmitter(QObject):
    log_emitted = Signal(str)


class QtLogStream(io.TextIOBase):
    def __init__(self, emitter: LogEmitter) -> None:
        super().__init__()
        self.emitter = emitter
        self._buffer = ""

    def write(self, text: str) -> int:
        if not text:
            return 0
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self.emitter.log_emitted.emit(line)
        return len(text)

    def flush(self) -> None:
        if self._buffer:
            self.emitter.log_emitted.emit(self._buffer)
            self._buffer = ""


class ServiceWorker(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.log_emitter = LogEmitter()

    def run(self) -> None:
        stream = QtLogStream(self.log_emitter)
        try:
            with redirect_stdout(stream), redirect_stderr(stream):
                result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # pragma: no cover - GUI async path
            stream.flush()
            error_detail = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            ).strip()
            self.signals.failed.emit(error_detail)
            return
        stream.flush()
        self.signals.finished.emit(result)


class FrontendController(QObject):
    state_changed = Signal(dict)
    message_changed = Signal(str, bool)
    log_message = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.config_service = ConfigService()
        self.pipeline_service = PipelineService()
        self.artifact_service = ArtifactService()
        self.geometry_preview_service = GeometryPreviewService()
        self.state = AppState()
        self.thread_pool = QThreadPool.globalInstance()
        self.log_lines: list[str] = []
        self.log_file_path: Path | None = None
        self.geometry_persist_timer = QTimer(self)
        self.geometry_persist_timer.setSingleShot(True)
        self.geometry_persist_timer.timeout.connect(self._flush_geometry_preferences)

    def clear_logs(self) -> None:
        self.log_lines.clear()
        self.log_message.emit("")
        if self.log_file_path is not None:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_file_path.write_text("", encoding="utf-8")

    def get_logs(self) -> str:
        return "\n".join(self.log_lines)

    def initialize(self) -> None:
        payload = self.config_service.initialize()
        self.state.current_device = payload.get("device_state")
        self.state.conv_defaults = self.config_service.load_conv_defaults()
        self.state.prompt_config = self.config_service.load_prompt_config()
        self.state.route_config = self.config_service.load_route_config()
        if self.state.current_device:
            self.state.device_config = self.state.current_device.get("device_config")
            self._apply_geometry_preferences_from_device_config()
            self.refresh_artifacts()
            self.refresh_simulation_files()
            self.refresh_geometry_area_result()
            self._set_message("已恢复上次器件上下文。")
        else:
            self._set_message("尚未选择器件，请先载入输入文件。")
        self._notify()

    def set_active_panel(self, panel: str) -> None:
        self.state.active_panel = panel
        self._notify()

    def set_mode(self, mode: str) -> None:
        self.state.mode = mode
        self._set_message(f"运行模式已切换为 {mode}。")
        self._notify()

    def select_device(self, input_file: str) -> None:
        self._flush_geometry_preferences()
        device = self.config_service.select_device(input_file)
        self.state.current_device = device
        self.state.device_config = device.get("device_config")
        self._apply_geometry_preferences_from_device_config()
        self.state.config_dirty = False
        self.state.conv_defaults_dirty = False
        self.state.prompt_dirty = False
        self.state.opened_artifact = None
        self.state.artifact_content = ""
        self.state.artifact_dirty = False
        self.state.opened_simulation_file = None
        self.state.simulation_content = ""
        self.state.simulation_dirty = False
        self.refresh_artifacts()
        self.refresh_simulation_files()
        self.refresh_geometry_area_result()
        self.state.active_panel = "config"
        self._set_message(f"器件已加载：{device['device_name']}")
        self._notify()

    def reload_config(self) -> None:
        self._flush_geometry_preferences()
        if self.state.has_device:
            input_file = self._current_input_file()
            self.state.device_config = self.config_service.load_device_config(input_file)
            self._apply_geometry_preferences_from_device_config()
        self.state.conv_defaults = self.config_service.load_conv_defaults()
        self.state.prompt_config = self.config_service.load_prompt_config()
        self.state.route_config = self.config_service.load_route_config()
        self.state.config_dirty = False
        self.state.route_dirty = False
        self.state.conv_defaults_dirty = False
        self.state.prompt_dirty = False
        self._set_message("配置已读取。")
        self._notify()

    def update_config(self, config_data: dict[str, Any]) -> None:
        self.state.device_config = deepcopy(config_data)
        self.state.config_dirty = True
        self._notify()

    def update_route_config(self, route_config: dict[str, Any]) -> None:
        self.state.route_config = deepcopy(route_config)
        self.state.route_dirty = True
        self._notify()

    def update_conv_defaults(self, conv_defaults: dict[str, Any]) -> None:
        self.state.conv_defaults = deepcopy(conv_defaults)
        self.state.conv_defaults_dirty = True
        self._notify()

    def update_prompt_config(self, prompt_config: dict[str, dict[str, str]]) -> None:
        self.state.prompt_config = deepcopy(prompt_config)
        self.state.prompt_dirty = True
        self._notify()

    def save_config(
        self,
        config_data: dict[str, Any] | None,
        route_config: dict[str, Any] | None,
        conv_defaults: dict[str, Any] | None,
        prompt_config: dict[str, dict[str, str]] | None = None,
    ) -> None:
        if self.state.has_device and config_data is not None:
            input_file = self._current_input_file()
            self.config_service.save_device_config(input_file, config_data)
            self.state.device_config = deepcopy(config_data)
            self.state.config_dirty = False
        if route_config is not None:
            self.config_service.save_route_config(route_config)
            self.state.route_config = deepcopy(route_config)
            self.state.route_dirty = False
        if conv_defaults is not None:
            self.config_service.save_conv_defaults(conv_defaults)
            self.state.conv_defaults = deepcopy(conv_defaults)
            self.state.conv_defaults_dirty = False
        if prompt_config is not None:
            self.config_service.save_prompt_config(prompt_config)
            self.state.prompt_config = deepcopy(prompt_config)
            self.state.prompt_dirty = False
        self._set_message("配置已保存。")
        self._notify()

    def _apply_geometry_preferences_from_device_config(self) -> None:
        preview = (self.state.device_config or {}).get("geometry_preview", {})
        self.state.geometry_aspect_ratio = min(
            max(float(preview.get("aspect_ratio", 1.0) or 1.0), 0.001),
            1000.0,
        )
        self.state.geometry_resolution_scale = min(
            max(float(preview.get("resolution_scale", 1.0) or 1.0), 0.5),
            6.0,
        )

    def _persist_geometry_preferences(self) -> None:
        if not self.state.has_device:
            return
        if self.state.device_config is None:
            self.state.device_config = {}
        self.state.device_config["geometry_preview"] = {
            "aspect_ratio": self.state.geometry_aspect_ratio,
            "resolution_scale": self.state.geometry_resolution_scale,
        }
        if self.state.current_device is not None:
            self.state.current_device["device_config"] = deepcopy(self.state.device_config)
        self.geometry_persist_timer.start(300)

    def _flush_geometry_preferences(self) -> None:
        if self.geometry_persist_timer.isActive():
            self.geometry_persist_timer.stop()
        if not self.state.has_device:
            return
        input_file = self._current_input_file()
        if self.state.device_config is None:
            self.state.device_config = self.config_service.load_device_config(input_file)
        self.state.device_config["geometry_preview"] = {
            "aspect_ratio": self.state.geometry_aspect_ratio,
            "resolution_scale": self.state.geometry_resolution_scale,
        }
        self.config_service.save_device_config(input_file, self.state.device_config)

    def refresh_artifacts(self) -> None:
        if not self.state.has_device:
            self.state.artifacts = []
            self._notify()
            return
        artifacts = self.artifact_service.list_artifacts(
            input_file=self._current_input_file()
        )
        source_path = self._current_input_file()
        artifacts.insert(
            0,
            {
                "key": "source_m2d",
                "path": source_path,
                "exists": True,
                "kind": Path(source_path).suffix.lower().lstrip(".") or "text",
            },
        )
        self.state.artifacts = artifacts
        self._notify()

    def open_artifact(self, path: str) -> None:
        artifact = self.artifact_service.read_artifact(path)
        self.state.opened_artifact = {
            "path": artifact["path"],
            "kind": artifact["kind"],
        }
        self.state.artifact_content = artifact["content"]
        self.state.artifact_dirty = False
        self._set_message(f"已打开文件：{path}")
        self._notify()

    def refresh_simulation_files(self) -> None:
        if not self.state.has_device:
            self.state.simulation_files = []
            self._notify()
            return
        simulation_dir = Path(self._current_input_file()).resolve().parent / "Simulation"
        files = []
        if simulation_dir.exists():
            for path in sorted(simulation_dir.glob("*.in")):
                files.append(
                    {
                        "key": path.name,
                        "path": str(path),
                        "exists": True,
                        "kind": "text",
                    }
                )
        self.state.simulation_files = files
        self._notify()

    def refresh_geometry_area_result(self) -> None:
        if not self.state.has_device:
            self.state.geometry_area_result = None
            self.state.geometry_source_path = ""
            self.state.geometry_preview_path = ""
            self.state.geometry_preview_kind = "pec"
            self._notify()
            return

        result = self.geometry_preview_service.load_geometry_area_result(
            self.state.current_device["device_name"]
        )
        self.state.geometry_source_path = result["source_path"]
        self.state.geometry_area_result = result["area_result"]
        self.state.geometry_preview_path = ""
        self._notify()

    def generate_pointset_file(self) -> None:
        if not self.state.has_device:
            self._set_error("当前没有器件，无法生成点集。")
            self._notify()
            return

        try:
            result = self.geometry_preview_service.generate_pointset_file(
                self.state.current_device["device_name"]
            )
        except Exception as exc:
            self._set_error(str(exc))
            self._notify()
            return
        self.state.pointset_path = result["path"]
        self.state.pointset_rows = result["rows"]
        self._set_message(f"点集文件已生成：{result['path']}")
        self._notify()

    def load_pointset_file(self) -> None:
        if not self.state.has_device:
            self.state.pointset_path = ""
            self.state.pointset_rows = []
            self._notify()
            return
        result = self.geometry_preview_service.load_pointset_file(
            self.state.current_device["device_name"]
        )
        self.state.pointset_path = result["path"]
        self.state.pointset_rows = result["rows"]
        self._notify()

    def set_geometry_aspect_ratio(self, ratio: float) -> None:
        safe_ratio = min(max(float(ratio), 0.001), 1000.0)
        if abs(self.state.geometry_aspect_ratio - safe_ratio) < 1e-9:
            return
        self.state.geometry_aspect_ratio = safe_ratio
        self._persist_geometry_preferences()
        if self.state.geometry_preview_path and self.state.geometry_area_result:
            self.generate_geometry_preview(self.state.geometry_preview_kind)
            return
        self._notify()

    def set_geometry_resolution_scale(self, scale: float) -> None:
        safe_scale = min(max(float(scale), 0.5), 6.0)
        if abs(self.state.geometry_resolution_scale - safe_scale) < 1e-9:
            return
        self.state.geometry_resolution_scale = safe_scale
        self._persist_geometry_preferences()
        if self.state.geometry_preview_path and self.state.geometry_area_result:
            self.generate_geometry_preview(self.state.geometry_preview_kind)
            return
        self._notify()

    def clear_geometry_preview(self) -> None:
        self.state.geometry_preview_path = ""
        self._notify()

    def generate_geometry_preview(self, preview_kind: str = "pec") -> None:
        if not self.state.has_device:
            self._set_error("当前没有器件，无法绘制图形。")
            self._notify()
            return

        area_result = self.state.geometry_area_result
        if not isinstance(area_result, dict) or not area_result:
            self._set_error("当前没有可用于绘制的 area_cac_result 数据。")
            self._notify()
            return

        try:
            result = self.geometry_preview_service.generate_geometry_preview(
                self.state.current_device["device_name"],
                area_result,
                preview_kind,
                self.state.geometry_aspect_ratio,
                self.state.geometry_resolution_scale,
            )
        except Exception as exc:
            self._set_error(str(exc))
            self._notify()
            return
        self.state.geometry_preview_path = result["path"]
        self.state.geometry_preview_kind = result["preview_kind"]
        self._set_message(f"图形预览已生成：{result['path']}")
        self._notify()

    def open_simulation_file(self, path: str) -> None:
        artifact = self.artifact_service.read_artifact(path)
        self.state.opened_simulation_file = {
            "path": artifact["path"],
            "kind": artifact["kind"],
        }
        self.state.simulation_content = artifact["content"]
        self.state.simulation_dirty = False
        self._set_message(f"已打开仿真文件：{path}")
        self._notify()

    def update_simulation_content(self, content: str) -> None:
        self.state.simulation_content = content
        self.state.simulation_dirty = True
        self._notify()

    def save_opened_simulation_file(self) -> None:
        if not self.state.opened_simulation_file:
            raise ValueError("当前没有打开的仿真文件。")
        result = self.artifact_service.save_artifact(
            self.state.opened_simulation_file["path"],
            self.state.simulation_content,
            validate=False,
        )
        if not result["ok"]:
            self._set_error(result["message"])
            self._notify()
            return
        self.state.simulation_dirty = False
        self.refresh_simulation_files()
        self._set_message("仿真文件已保存。")
        self._notify()

    def update_artifact_content(self, content: str) -> None:
        self.state.artifact_content = content
        self.state.artifact_dirty = True
        self._notify()

    def save_opened_artifact(self, validate: bool = True) -> None:
        if not self.state.opened_artifact:
            raise ValueError("当前没有打开的产物。")
        result = self.artifact_service.save_artifact(
            self.state.opened_artifact["path"],
            self.state.artifact_content,
            validate=validate,
        )
        if not result["ok"]:
            self._set_error(result["message"])
            self._notify()
            return
        self.state.artifact_dirty = False
        hint = self.suggest_next_step_for_artifact(self.state.opened_artifact["path"])
        message = "文件已保存。"
        if hint:
            message = f"{message} {hint}"
        self.refresh_artifacts()
        self._set_message(message)
        self._notify()

    def run_step(self, step: int) -> None:
        if not self.state.can_run:
            self._set_error("当前尚不可执行转译，请先完成器件选择与配置读取。")
            self._notify()
            return
        self._run_async(
            self.pipeline_service.run_step,
            self._handle_run_success,
            mode=self.state.mode,
            step=step,
            input_file=self._current_input_file(),
        )

    def run_pipeline(self) -> None:
        if not self.state.can_run:
            self._set_error("当前尚不可执行转译，请先完成器件选择与配置读取。")
            self._notify()
            return
        self._run_async(
            self.pipeline_service.run_pipeline,
            self._handle_run_success,
            mode=self.state.mode,
            input_file=self._current_input_file(),
        )

    def suggest_next_step_for_artifact(self, path: str) -> str:
        normalized = path.replace("\\", "/").lower()
        if normalized.endswith("parsed_result.json"):
            return "建议从 Step 3 继续执行。"
        if normalized.endswith("mid_round1.json"):
            return "建议从 Step 4 继续执行。"
        if normalized.endswith("mid_round2.json"):
            return "建议从 Step 5 继续执行。"
        return ""

    def _run_async(
        self,
        fn: Callable[..., Any],
        on_success: Callable[[Any], None],
        **kwargs: Any,
    ) -> None:
        self.state.is_running = True
        self.state.last_run_result = None
        self.log_file_path = self._resolve_log_file_path()
        self.clear_logs()
        self._append_log("[system] task started")
        self._set_message("正在执行，请稍候。")
        self._notify()

        worker = ServiceWorker(fn, **kwargs)
        worker.log_emitter.log_emitted.connect(self._append_log)
        worker.signals.finished.connect(on_success)
        worker.signals.failed.connect(self._handle_run_failure)
        self.thread_pool.start(worker)

    def _handle_run_success(self, result: Any) -> None:
        self.state.is_running = False
        self.state.last_run_result = result
        self._append_log("[system] task finished")
        self.refresh_artifacts()
        self.refresh_simulation_files()
        self.refresh_geometry_area_result()
        step_name = result.get("step_name") or "pipeline"
        self._set_message(f"执行完成：{step_name}")
        self._notify()

    def _handle_run_failure(self, error: str) -> None:
        self.state.is_running = False
        self.state.last_run_result = {
            "ok": False,
            "error": error,
        }
        self._append_log(f"[error] {error}")
        self._set_error(self._summarize_error(error))
        self._notify()

    def _current_input_file(self) -> str:
        if not self.state.current_device:
            raise ValueError("尚未选择器件。")
        return self.state.current_device["input_file"]

    def _set_message(self, message: str) -> None:
        self.state.message = message
        self.state.error_message = ""
        self.message_changed.emit(message, False)

    def _set_error(self, message: str) -> None:
        self.state.error_message = message
        self.state.message = ""
        self.message_changed.emit(message, True)

    def _append_log(self, message: str) -> None:
        self.log_lines.append(message)
        if self.log_file_path is not None:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file_path, "a", encoding="utf-8") as fh:
                fh.write(message + "\n")
        self.log_message.emit(message)

    def _notify(self) -> None:
        self.state_changed.emit(self.state.snapshot())

    def _resolve_log_file_path(self) -> Path | None:
        if not self.state.current_device:
            return None
        workdir = self.state.current_device.get("workdir")
        if not workdir:
            return None
        return Path(workdir) / "frontend_run.log"

    def _summarize_error(self, error: str) -> str:
        lines = [line.strip() for line in error.splitlines() if line.strip()]
        if not lines:
            return "运行失败。"
        for line in reversed(lines):
            if not line.startswith("File "):
                return f"运行失败：{line}"
        return f"运行失败：{lines[-1]}"
