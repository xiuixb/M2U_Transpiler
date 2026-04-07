import json
from pathlib import Path
from typing import Any

from src.domain.config.m2u_convconst import init_constants
from src.application.services.config_service import ConfigService


class ArtifactService:
    """
    中间产物服务：
    - 列出当前器件的已知中间产物
    - 读取/保存产物
    - 提供基础 JSON/JSONL 校验
    """

    def __init__(self):
        self.config_service = ConfigService()

    def list_artifacts(self, device_name: str | None = None, input_file: str | None = None) -> list[dict[str, Any]]:
        resolved_input = self._resolve_input_file(device_name=device_name, input_file=input_file)
        constants = init_constants(Path(resolved_input).resolve().parent.name)
        artifact_map = [
            ("preprocessed", constants.pre_jsonl),
            ("parsed", constants.parsed_json),
            ("mid_round1", constants.mid_symbol1_json),
            ("mid_round2", constants.mid_symbol2_json),
            ("mid_symbols", constants.mid_symbols_json),
            ("llmconv", constants.llmconv_json),
            ("llm_prompt", constants.llm_prompt_txt),
            ("llm_io_log", constants.llm_io_dir),
            ("variables", constants.symbols_json),
            ("uni_symbols", constants.uni_symbols_json),
        ]
        artifacts = []
        for key, path in artifact_map:
            artifacts.append({
                "key": key,
                "path": str(path),
                "exists": path.exists(),
                "kind": self._guess_kind(path),
            })
        return artifacts

    def read_artifact(self, path: str) -> dict[str, Any]:
        artifact_path = Path(path)
        if not artifact_path.exists():
            raise FileNotFoundError(f"中间产物不存在: {artifact_path}")

        with open(artifact_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "path": str(artifact_path),
            "kind": self._guess_kind(artifact_path),
            "content": content,
        }

    def save_artifact(self, path: str, content: str, validate: bool = True) -> dict[str, Any]:
        artifact_path = Path(path)
        kind = self._guess_kind(artifact_path)
        validation = self.validate_content(content, kind) if validate else {"ok": True, "message": "skip validation"}
        if validate and not validation["ok"]:
            return {
                "ok": False,
                "path": str(artifact_path),
                "message": validation["message"],
            }

        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with open(artifact_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "ok": True,
            "path": str(artifact_path),
            "kind": kind,
            "message": "saved",
        }

    def validate_content(self, content: str, kind: str) -> dict[str, Any]:
        try:
            if kind == "json":
                json.loads(content)
            elif kind == "jsonl":
                for line_no, line in enumerate(content.splitlines(), start=1):
                    line = line.strip()
                    if line:
                        json.loads(line)
            return {"ok": True, "message": "valid"}
        except Exception as exc:
            return {"ok": False, "message": f"invalid {kind}: {exc}"}

    def _guess_kind(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            return "jsonl"
        if suffix == ".json":
            return "json"
        if suffix == ".txt":
            return "text"
        return "text"

    def _resolve_input_file(self, device_name: str | None, input_file: str | None) -> str:
        if input_file:
            return str(Path(input_file).resolve())
        current_input = self.config_service.get_current_input_file()
        if current_input:
            return current_input
        if device_name:
            data_dir = Path(__file__).resolve().parents[3] / "data" / device_name
            candidates = sorted(data_dir.glob("*.m2d")) or sorted(data_dir.glob("*.mcl"))
            if candidates:
                return str(candidates[0].resolve())
        raise ValueError("未提供 input_file，且 sys_config.json 中没有当前器件路径")
