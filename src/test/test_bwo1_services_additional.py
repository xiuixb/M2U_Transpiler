import json
import unittest
from pathlib import Path

from src.application.services import ArtifactService, ConfigService, PipelineService
from src.infrastructure.sys_config import SysConfigStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "BWO1" / "BWO1.m2d"
SRC_ROOT = PROJECT_ROOT / "src"
SRC_SYS_CONFIG = SRC_ROOT / "sys_config.json"


class TestBWO1ServicesAdditional(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_file = str(INPUT_FILE.resolve())
        cls.workdir = INPUT_FILE.parent / "workdir"
        cls.device_config_path = cls.workdir / "m2u_config.json"
        cls.invalid_json_path = cls.workdir / "invalid_service_test.json"

        cls.config_service = ConfigService()
        cls.pipeline_service = PipelineService()
        cls.artifact_service = ArtifactService()
        cls.sys_store = SysConfigStore(SRC_ROOT)

        cls._sys_config_backup = (
            SRC_SYS_CONFIG.read_text(encoding="utf-8") if SRC_SYS_CONFIG.exists() else None
        )
        cls._device_config_backup = (
            cls.device_config_path.read_text(encoding="utf-8")
            if cls.device_config_path.exists()
            else None
        )

        cls.config_service.select_device(cls.input_file)

    @classmethod
    def tearDownClass(cls):
        if cls.invalid_json_path.exists():
            cls.invalid_json_path.unlink()

        if cls._device_config_backup is None:
            if cls.device_config_path.exists():
                cls.device_config_path.unlink()
        else:
            cls.device_config_path.write_text(cls._device_config_backup, encoding="utf-8")

        if cls._sys_config_backup is None:
            if SRC_SYS_CONFIG.exists():
                SRC_SYS_CONFIG.unlink()
        else:
            SRC_SYS_CONFIG.write_text(cls._sys_config_backup, encoding="utf-8")

    def test_01_sys_config_store_set_and_get_current_input(self):
        self.sys_store.set_current_input_file(self.input_file, "BWO1")

        config = self.sys_store.load()
        self.assertEqual(config["current_input_file"], self.input_file)
        self.assertEqual(config["last_device_name"], "BWO1")
        self.assertEqual(self.sys_store.get_current_input_file(), self.input_file)

    def test_02_config_service_save_and_getters(self):
        config = self.config_service.load_device_config(self.input_file)
        config["runtime"]["IF_Conv2Void"] = not config["runtime"]["IF_Conv2Void"]

        saved_path = self.config_service.save_device_config(self.input_file, config)
        loaded = self.config_service.load_device_config(self.input_file)

        self.assertEqual(saved_path, self.device_config_path)
        self.assertEqual(loaded["runtime"]["IF_Conv2Void"], config["runtime"]["IF_Conv2Void"])
        self.assertEqual(self.config_service.get_current_input_file(), self.input_file)
        self.assertEqual(
            self.config_service.get_device_config_path(self.input_file),
            self.device_config_path,
        )

    def test_03_initialize_clears_missing_current_input(self):
        missing_file = str((PROJECT_ROOT / "data" / "BWO1" / "missing_device.m2d").resolve())
        self.config_service.save_system_config(
            {"current_input_file": missing_file, "last_device_name": "BWO1"}
        )

        state = self.config_service.initialize()

        self.assertEqual(state["system_config"]["current_input_file"], "")
        self.assertIsNone(state["device_state"])

        restored = self.config_service.select_device(self.input_file)
        self.assertEqual(restored["device_name"], "BWO1")

    def test_04_pipeline_service_can_restore_input_from_sys_config(self):
        self.config_service.select_device(self.input_file)

        result = self.pipeline_service.run_step(mode="llm", step=1, input_file=None)

        self.assertTrue(result["ok"])
        self.assertEqual(result["input_file"], self.input_file)
        self.assertTrue(Path(result["artifacts"]["pre_jsonl"]).exists())

    def test_05_pipeline_service_ply_full_pipeline(self):
        result = self.pipeline_service.run_pipeline(mode="ply", input_file=self.input_file)

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "ply")
        self.assertEqual(result["device_name"], "BWO1")
        self.assertTrue(Path(result["artifacts"]["parsed_json"]).exists())
        self.assertTrue(Path(result["artifacts"]["uni_symbols_json"]).exists())

    def test_06_pipeline_service_error_branches(self):
        with self.assertRaises(ValueError):
            self.pipeline_service.run_pipeline(mode="bad_mode", input_file=self.input_file)

        with self.assertRaises(ValueError):
            self.pipeline_service.run_step(mode="llm", step=9, input_file=self.input_file)

        with self.assertRaises(ValueError):
            self.pipeline_service.run_step(mode="llm", step=999, input_file=self.input_file)

        with self.assertRaises(NotImplementedError):
            self.pipeline_service.run_step(mode="ply", step=1, input_file=self.input_file)

    def test_07_artifact_service_recovery_and_validation_branches(self):
        self.config_service.select_device(self.input_file)

        artifacts_from_sys = self.artifact_service.list_artifacts()
        artifacts_from_device = self.artifact_service.list_artifacts(device_name="BWO1")

        self.assertGreater(len(artifacts_from_sys), 0)
        self.assertGreater(len(artifacts_from_device), 0)

        invalid = self.artifact_service.save_artifact(
            str(self.invalid_json_path),
            '{"bad": }',
            validate=True,
        )
        self.assertFalse(invalid["ok"])

        no_validate = self.artifact_service.save_artifact(
            str(self.invalid_json_path),
            '{"bad": }',
            validate=False,
        )
        self.assertTrue(no_validate["ok"])

        with self.assertRaises(FileNotFoundError):
            self.artifact_service.read_artifact(str(self.workdir / "not_exists.json"))

        validation = self.artifact_service.validate_content('{"ok": 1}', "json")
        self.assertTrue(validation["ok"])


if __name__ == "__main__":
    unittest.main()
