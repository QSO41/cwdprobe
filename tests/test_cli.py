import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cwdprobe-reports-")
        self.addCleanup(self.temp.cleanup)
        self.counter = 0

    def cli(self, *args):
        self.counter += 1
        report = Path(self.temp.name) / str(self.counter)
        p = subprocess.run([sys.executable, "-m", "cwdprobe", "--root",
                            os.environ["CWDPROBE_TEST_ROOT"], "--report", str(report),
                            *args], cwd=PROJECT, capture_output=True, timeout=30)
        self.assertTrue((report / "report.json").is_file(), p.stderr.decode(errors="replace"))
        return p, json.loads((report / "report.json").read_text(encoding="utf-8"))

    def test_good_demo_io_all_cases_twice(self):
        p, r = self.cli("--demo", "good")
        self.assertEqual(p.returncode, 0, r)
        self.assertEqual(r["summary"]["status"], "PASS")
        self.assertEqual(len(r["results"]), 12)
        self.assertEqual({x["case"] for x in r["results"]},
                         {"ascii", "chinese", "japanese", "korean", "spaces", "symbols"})
        for x in r["results"]:
            self.assertEqual(x["stdout"]["text"], "roundtrip-ok\n")
        self.assertEqual(r["cleanup"]["status"], "PASS")
        self.assertFalse(Path(r["workspace"]).exists())

    def test_simulated_path_failure(self):
        p, r = self.cli("--demo", "ascii-only")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(r["summary"]["finding"], "PATH_SENSITIVE_FAILURE")
        self.assertEqual([x["exit_code"] for x in r["results"][:6]], [0, 23, 23, 23, 0, 0])

    def test_simulated_general_failure(self):
        p, r = self.cli("--demo", "always-fail")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(r["summary"]["finding"], "GENERAL_FAILURE")

    def test_invalid_command_not_unicode_failure(self):
        p, r = self.cli("--", "not-a-real-cwdprobe-command-7519")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(r["summary"]["status"], "TOOL_ERROR")

    def test_cwd_output_difference_and_explicit_normalization(self):
        command = ["--", sys.executable, "-c", "import os; os.write(1,os.getcwd().encode('utf-8'))"]
        p, r = self.cli(*command)
        self.assertEqual(p.returncode, 3)
        self.assertEqual(r["summary"]["finding"], "OUTPUT_DIFFERENCE")
        p, r = self.cli("--normalize-cwd", *command)
        self.assertEqual(p.returncode, 0, r)
        self.assertTrue(r["settings"]["normalize_cwd"])

    def test_unicode_root_refused_before_any_command(self):
        p, r = self.cli("--root", str(PROJECT), "--demo", "good")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(r["results"], [])

    def test_timeout_and_output_limit_are_inconclusive(self):
        for opts, code, state in [(["--timeout", "0.1"], "import time; time.sleep(20)", "TIMEOUT"),
                                  (["--max-bytes", "128"], "print('x'*10000)", "OUTPUT_LIMIT")]:
            with self.subTest(state=state):
                p, r = self.cli(*opts, "--", sys.executable, "-c", code)
                self.assertEqual(p.returncode, 3)
                self.assertEqual(r["results"][0]["state"], state)
                self.assertEqual(r["cleanup"]["status"], "PASS")

    def test_report_never_overwrites_existing_directory(self):
        report = Path(self.temp.name) / "existing"
        report.mkdir()
        sentinel = report / "report.json"
        sentinel.write_text("keep", encoding="ascii")
        p = subprocess.run([sys.executable, "-m", "cwdprobe", "--root",
                            os.environ["CWDPROBE_TEST_ROOT"], "--report", str(report),
                            "--demo", "good"], cwd=PROJECT, capture_output=True, timeout=10)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(sentinel.read_text(), "keep")
