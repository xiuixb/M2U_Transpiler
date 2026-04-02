import json
import unittest
from pathlib import Path

import os
import sys
# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from src.application.services import ArtifactService, ConfigService, PipelineService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "BWO1" / "BWO1.m2d"
SRC_SYS_CONFIG = PROJECT_ROOT / "src" / "sys_config.json"


class TestBWO1Services(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_file = str(INPUT_FILE.resolve())
        cls.device_dir = INPUT_FILE.parent
        cls.workdir = cls.device_dir / "workdir"
        cls.device_config_path = cls.workdir / "m2u_config.json"
        cls.temp_artifact_path = cls.workdir / "service_test_artifact.json"

        cls.config_service = ConfigService()
        cls.pipeline_service = PipelineService()
        cls.artifact_service = ArtifactService()

        cls._sys_config_backup = (
            SRC_SYS_CONFIG.read_text(encoding="utf-8") if SRC_SYS_CONFIG.exists() else None
        )

    @classmethod
    def tearDownClass(cls):
        if cls.temp_artifact_path.exists():
            cls.temp_artifact_path.unlink()

        if cls._sys_config_backup is None:
            if SRC_SYS_CONFIG.exists():
                SRC_SYS_CONFIG.unlink()
            return

        SRC_SYS_CONFIG.write_text(cls._sys_config_backup, encoding="utf-8")

    def test_01_initialize_returns_system_state(self):
        state = self.config_service.initialize()

        self.assertIn("system_config_path", state)
        self.assertTrue(state["system_config_path"].endswith(r"src\sys_config.json"))
        self.assertIn("system_config", state)

    def test_02_select_device_creates_workdir_and_device_config(self):
        state = self.config_service.select_device(self.input_file)

        self.assertEqual(state["device_name"], "BWO1")
        self.assertEqual(Path(state["input_file"]), INPUT_FILE.resolve())
        self.assertTrue(self.workdir.exists())
        self.assertTrue(self.device_config_path.exists())

        sys_config = json.loads(SRC_SYS_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(sys_config["current_input_file"], self.input_file)
        self.assertEqual(sys_config["last_device_name"], "BWO1")

    def test_03_load_device_config_contains_expected_sections(self):
        config = self.config_service.load_device_config(self.input_file)

        self.assertEqual(config["device_name"], "BWO1")
        self.assertIn("paths", config)
        self.assertIn("runtime", config)
        self.assertIn("debug", config)
        self.assertEqual(config["input_file"], self.input_file)

    def test_04_artifact_service_can_list_known_artifacts(self):
        artifacts = self.artifact_service.list_artifacts(input_file=self.input_file)
        artifact_keys = {item["key"] for item in artifacts}

        self.assertIn("parsed", artifact_keys)
        self.assertIn("mid_symbol1", artifact_keys)
        self.assertIn("uni_symbols", artifact_keys)

    def test_05_artifact_service_can_save_and_read_json(self):
        content = json.dumps({"device": "BWO1", "ok": True}, ensure_ascii=False, indent=2)
        save_result = self.artifact_service.save_artifact(
            str(self.temp_artifact_path),
            content,
            validate=True,
        )
        read_result = self.artifact_service.read_artifact(str(self.temp_artifact_path))

        self.assertTrue(save_result["ok"])
        self.assertEqual(read_result["kind"], "json")
        self.assertEqual(json.loads(read_result["content"])["device"], "BWO1")

    def test_06_pipeline_service_reports_supported_modes(self):
        self.assertTrue(self.pipeline_service.supports_step("llm"))
        self.assertFalse(self.pipeline_service.supports_step("ply"))

        llm_steps = self.pipeline_service.list_steps("llm")
        ply_steps = self.pipeline_service.list_steps("ply")

        self.assertEqual(llm_steps[-1]["step"], 9)
        self.assertEqual(ply_steps, [{"step": 9, "name": "pipeline"}])

    def test_07_pipeline_service_can_run_full_llm_pipeline(self):
        result = self.pipeline_service.run_pipeline(mode="llm", input_file=self.input_file)

        self.assertTrue(result["ok"])
        self.assertEqual(result["device_name"], "BWO1")
        self.assertEqual(result["step"], 9)
        self.assertIn("artifacts", result)
        self.assertTrue(Path(result["artifacts"]["parsed_json"]).exists())
        self.assertTrue(Path(result["artifacts"]["mid_symbol1_json"]).exists())
        self.assertTrue(Path(result["artifacts"]["mid_symbol2_json"]).exists())
        self.assertTrue(Path(result["artifacts"]["uni_symbols_json"]).exists())


if __name__ == "__main__":
    unittest.main()
