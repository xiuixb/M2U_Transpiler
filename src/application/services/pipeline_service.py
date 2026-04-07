import time
from pathlib import Path
from typing import Any

from src.application.magic2unipic import MAGIC2UNIPIC as PlyPipeline
from src.application.m2u_llm_menu import MAGIC2UNIPIC as LlmPipelineMenu
from src.application.services.config_service import ConfigService
from src.domain.config.m2u_convconst import init_constants


class PipelineService:
    """
    前端调用的统一流水线服务。

    说明：
    - `llm` 模式支持整体流水线和分阶段执行
    - `ply` 模式当前支持整体流水线；单步执行后续可继续补齐
    """

    STEP_LABELS = {
        1: "preprocess",
        2: "parse",
        3: "convert_round1",
        4: "convert_round2",
        5: "generate_files",
        9: "pipeline",
    }

    def __init__(self) -> None:
        self.config_service = ConfigService()

    def run_pipeline(self, mode: str, input_file: str | None = None) -> dict[str, Any]:
        input_path = Path(self._resolve_input_file(input_file)).resolve()
        device_name = input_path.parent.name
        constants = init_constants(device_name)
        timings = self._empty_timings()

        if mode == "ply":
            started = time.perf_counter()
            pipeline = PlyPipeline(str(input_path))
            pipeline.m2u_pipeline()
            timings["total"] = time.perf_counter() - started
        elif mode == "llm":
            pipeline = LlmPipelineMenu(str(input_path))

            preprocess_started = time.perf_counter()
            pipeline.step_preprocess()
            timings["preprocess"] = time.perf_counter() - preprocess_started

            parse_started = time.perf_counter()
            pipeline.step_parse()
            timings["parse"] = time.perf_counter() - parse_started

            conv1_started = time.perf_counter()
            pipeline.step_convert_round1()
            timings["conv_round1"] = time.perf_counter() - conv1_started

            conv2_started = time.perf_counter()
            pipeline.step_convert_round2()
            timings["conv_round2"] = time.perf_counter() - conv2_started

            generate_started = time.perf_counter()
            pipeline.step_convert_round3_and_generate()
            timings["generate"] = time.perf_counter() - generate_started

            timings["total"] = sum(
                value for value in timings.values() if isinstance(value, (int, float))
            )
            print(f"{'Parse':<15}: {timings['parse']:.2f}s")
            print(f"{'Conv round1':<15}: {timings['conv_round1']:.2f}s")
            print(f"{'Conv round2':<15}: {timings['conv_round2']:.2f}s")
            print(f"{'Generate':<15}: {timings['generate']:.2f}s")
            print(f"{'Total time':<15}: {timings['total']:.2f}s")
        else:
            raise ValueError(f"不支持的模式: {mode}")

        return {
            "ok": True,
            "mode": mode,
            "step": 9,
            "step_name": self.STEP_LABELS[9],
            "input_file": str(input_path),
            "device_name": device_name,
            "timings": timings,
            "artifacts": self._artifact_summary(constants),
        }

    def run_step(self, mode: str, step: int, input_file: str | None = None) -> dict[str, Any]:
        if step not in self.STEP_LABELS or step == 9:
            raise ValueError(f"不支持的步骤: {step}")

        input_path = Path(self._resolve_input_file(input_file)).resolve()
        device_name = input_path.parent.name
        constants = init_constants(device_name)
        timings = self._empty_timings()

        if mode == "llm":
            pipeline = LlmPipelineMenu(str(input_path))
            started = time.perf_counter()
            pipeline.run_step(step)
            elapsed = time.perf_counter() - started
            if step == 1:
                timings["preprocess"] = elapsed
            elif step == 2:
                timings["parse"] = elapsed
            elif step == 3:
                timings["conv_round1"] = elapsed
            elif step == 4:
                timings["conv_round2"] = elapsed
            elif step == 5:
                timings["generate"] = elapsed
            timings["total"] = elapsed
        elif mode == "ply":
            raise NotImplementedError("ply 模式的分阶段 service 还未实现")
        else:
            raise ValueError(f"不支持的模式: {mode}")

        return {
            "ok": True,
            "mode": mode,
            "step": step,
            "step_name": self.STEP_LABELS[step],
            "input_file": str(input_path),
            "device_name": device_name,
            "timings": timings,
            "artifacts": self._artifact_summary(constants),
        }

    def supports_step(self, mode: str) -> bool:
        return mode == "llm"

    def list_steps(self, mode: str) -> list[dict[str, Any]]:
        if mode == "llm":
            return [
                {"step": 1, "name": self.STEP_LABELS[1]},
                {"step": 2, "name": self.STEP_LABELS[2]},
                {"step": 3, "name": self.STEP_LABELS[3]},
                {"step": 4, "name": self.STEP_LABELS[4]},
                {"step": 5, "name": self.STEP_LABELS[5]},
                {"step": 9, "name": self.STEP_LABELS[9]},
            ]
        return [{"step": 9, "name": self.STEP_LABELS[9]}]

    def _artifact_summary(self, constants: Any) -> dict[str, str]:
        return {
            "pre_jsonl": str(constants.pre_jsonl),
            "parsed_json": str(constants.parsed_json),
            "mid_round1_json": str(constants.mid_symbol1_json),
            "mid_round2_json": str(constants.mid_symbol2_json),
            "mid_symbols_json": str(constants.mid_symbols_json),
            "llmconv_json": str(constants.llmconv_json),
            "uni_symbols_json": str(constants.uni_symbols_json),
            "infile_dir": str(constants.infile_dir),
        }

    def _empty_timings(self) -> dict[str, float | None]:
        return {
            "preprocess": None,
            "parse": None,
            "conv_round1": None,
            "conv_round2": None,
            "generate": None,
            "total": None,
        }

    def _resolve_input_file(self, input_file: str | None) -> str:
        if input_file:
            return str(Path(input_file).resolve())
        current_input = self.config_service.get_current_input_file()
        if current_input:
            return current_input
        raise ValueError("未提供 input_file，且 sys_config.json 中没有当前器件路径")
