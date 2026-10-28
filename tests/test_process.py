import json
import os
from pathlib import Path
import sys
import time
import unittest

from cwdprobe.workspace import Workspace

try:
    from cwdprobe.process import run_process
except ImportError:
    run_process = None


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace(Path(os.environ["CWDPROBE_TEST_ROOT"]))
        self.cwd = self.w.case("chinese", 1)

    def tearDown(self):
        self.w.cleanup()

    def run_child(self, code, args=(), timeout=3, cap=4096, encoding="utf-8"):
        self.assertTrue(callable(run_process), "native process runner is not implemented")
        return run_process([sys.executable, "-c", code, *args], self.cwd, timeout, cap, encoding)

    def test_literal_argv_empty_spaces_quotes_and_metacharacters(self):
        args = ["", "has space", "中文", 'a"b', "a&b", "$(echo nope)", "C:\\tail\\"]
        r = self.run_child("import sys,json; print(json.dumps(sys.argv[1:]))", args)
        self.assertEqual(r["state"], "COMPLETED")
        self.assertEqual(json.loads(r["stdout"]["text"]), args)

    def test_invalid_executable_is_launch_error(self):
        self.assertTrue(callable(run_process), "native process runner is not implemented")
        r = run_process(["C:\\does-not-exist-cwdprobe.exe"], self.cwd, 1, 4096, "utf-8")
        self.assertEqual(r["state"], "LAUNCH_ERROR")
        self.assertIsNone(r["exit_code"])

    def test_timeout_is_bounded(self):
        start = time.monotonic()
        r = self.run_child("import time; time.sleep(60)", timeout=0.3)
        self.assertEqual(r["state"], "TIMEOUT")
        self.assertLess(time.monotonic() - start, 5)

    def test_binary_decode_error_and_raw_evidence(self):
        import base64
        r = self.run_child("import os; os.write(1,b'\\xff\\xfe')")
        self.assertEqual(r["state"], "COMPLETED")
        self.assertTrue(r["stdout"]["decode_error"])
        self.assertEqual(base64.b64decode(r["stdout"]["raw_base64"]), b"\xff\xfe")
        self.assertIsNone(r["stdout"]["text"])

    def test_non_utf_codec_error_keeps_completed_bytes(self):
        import base64
        r = self.run_child("import os; os.write(1,b'!')", encoding="punycode")
        self.assertEqual(r["state"], "COMPLETED")
        self.assertTrue(r["stdout"]["decode_error"])
        self.assertEqual(base64.b64decode(r["stdout"]["raw_base64"]), b"!")

    def test_simultaneous_large_streams_are_capped(self):
        r = self.run_child("import os\nwhile True:\n os.write(1,b'x'*8192); os.write(2,b'y'*8192)", cap=1024)
        self.assertEqual(r["state"], "OUTPUT_LIMIT")
        self.assertLessEqual(r["stdout"]["stored_bytes"], 1024)
        self.assertLessEqual(r["stderr"]["stored_bytes"], 1024)
        self.assertTrue(r["stdout"]["truncated"] or r["stderr"]["truncated"])

    def test_timeout_kills_descendant_before_delayed_write(self):
        r = self.run_child(
            "import subprocess,sys,time; "
            "subprocess.Popen([sys.executable,'-c',"
            "\"import time,pathlib; time.sleep(1.2); pathlib.Path('escaped').write_text('bad')\"]); "
            "time.sleep(60)", timeout=0.5)
        self.assertEqual(r["state"], "TIMEOUT")
        time.sleep(1.3)
        self.assertFalse((self.cwd / "escaped").exists())

    def test_parent_exit_also_closes_descendant_pipe(self):
        start = time.monotonic()
        r = self.run_child(
            "import subprocess,sys; subprocess.Popen([sys.executable,'-c',"
            "\"import time,pathlib; time.sleep(1.2); pathlib.Path('escaped').write_text('bad')\"])")
        self.assertEqual((r["state"], r["exit_code"]), ("COMPLETED", 0))
        self.assertLess(time.monotonic() - start, 3)
        time.sleep(1.3)
        self.assertFalse((self.cwd / "escaped").exists())
