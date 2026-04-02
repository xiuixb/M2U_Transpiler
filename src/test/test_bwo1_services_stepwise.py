import json
import unittest
from pathlib import Path

from src.application.services import ConfigService, PipelineService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "BWO1" / "BWO1.m2d"
SRC_SYS_CONFIG = PROJECT_ROOT / "src" / "sys_config.json"


class TestBWO1ServicesStepwise(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_file = str(INPUT_FILE.resolve())
        cls.workdir = INPUT_FILE.parent / "workdir"
        cls.config_service = ConfigService()
        cls.pipeline_service = PipelineService()
        cls._sys_config_backup = (
            SRC_SYS_CONFIG.read_text(encoding="utf-8") if SRC_SYS_CONFIG.exists() else None
        )
        cls.config_service.select_device(cls.input_file)

    @classmethod
    def tearDownClass(cls):
        if cls._sys_config_backup is None:
            if SRC_SYS_CONFIG.exists():
                SRC_SYS_CONFIG.unlink()
            return
        SRC_SYS_CONFIG.write_text(cls._sys_config_backup, encoding="utf-8")

    def test_01_run_step_1_preprocess(self):
        result = self.pipeline_service.run_step(mode="llm", step=1, input_file=self.input_file)

        self.assertTrue(result["ok"])
        self.assertEqual(result["step"], 1)
        self.assertTrue(Path(result["artifacts"]["pre_jsonl"]).exists())

    def test_02_run_step_2_parse(self):
        result = self.pipeline_service.run_step(mode="llm", step=2, input_file=self.input_file)

        self.assertTrue(result["ok"])
        self.assertEqual(result["step"], 2)
        parsed_path = Path(result["artifacts"]["parsed_json"])
        self.assertTrue(parsed_path.exists())

        parsed_data = json.loads(parsed_path.read_text(encoding="utf-8"))
        self.assertIsInstance(parsed_data, list)
        self.assertGreater(len(parsed_data), 0)

    def test_03_run_step_3_convert_round1(self):
        result = self.pipeline_service.run_step(mode="llm", step=3, input_file=self.input_file)

        self.assertTrue(result["ok"])
        self.assertEqual(result["step"], 3)
        self.assertTrue(Path(result["artifacts"]["mid_symbol1_json"]).exists())
        self.assertTrue(Path(result["artifacts"]["llmconv_json"]).exists())

    def test_04_run_step_4_convert_round2(self):
        result = self.pipeline_service.run_step(mode="llm", step=4, input_file=self.input_file)

        self.assertTrue(result["ok"])
        self.assertEqual(result["step"], 4)
        self.assertTrue(Path(result["artifacts"]["mid_symbol2_json"]).exists())

    def test_05_run_step_5_generate_files(self):
        result = self.pipeline_service.run_step(mode="llm", step=5, input_file=self.input_file)

        self.assertTrue(result["ok"])
        self.assertEqual(result["step"], 5)

        uni_symbols = Path(result["artifacts"]["uni_symbols_json"])
        output_dir = Path(result["artifacts"]["infile_dir"])

        self.assertTrue(uni_symbols.exists())
        self.assertTrue(output_dir.exists())
        self.assertTrue((output_dir / "build.in").exists())
        self.assertTrue((output_dir / "FaceBnd.in").exists())


if __name__ == "__main__":
    unittest.main()
