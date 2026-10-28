import unittest

try:
    from cwdprobe.analysis import classify
except ImportError:
    classify = None


def row(case, code=0, state="COMPLETED", text="ok", repeat=1):
    return {"case": case, "repeat": repeat, "state": state,
            "exit_code": code, "stdout": {"text": text, "decode_error": None},
            "stderr": {"text": "", "decode_error": None}, "cwd": "C:\\x"}


class AnalysisTests(unittest.TestCase):
    def run_classify(self, rows, normalize=False):
        self.assertTrue(callable(classify), "classification is not implemented")
        return classify(rows, normalize)

    def test_path_specific_failure(self):
        r = self.run_classify([row("ascii"), row("chinese", 7)])
        self.assertEqual((r["status"], r["finding"]), ("FAIL", "PATH_SENSITIVE_FAILURE"))

    def test_all_fail_is_not_unicode_diagnosis(self):
        r = self.run_classify([row("ascii", 7), row("chinese", 7)])
        self.assertEqual(r["finding"], "GENERAL_FAILURE")

    def test_bad_baseline_is_inconclusive(self):
        r = self.run_classify([row("ascii", 7), row("chinese")])
        self.assertEqual((r["status"], r["finding"]), ("INCONCLUSIVE", "BASELINE_FAILURE"))

    def test_tool_and_incomplete_states(self):
        for state, status in [("LAUNCH_ERROR", "TOOL_ERROR"), ("TIMEOUT", "INCONCLUSIVE"),
                              ("OUTPUT_LIMIT", "INCONCLUSIVE")]:
            with self.subTest(state=state):
                r = self.run_classify([row("ascii"), row("chinese", None, state)])
                self.assertEqual(r["status"], status)

    def test_output_difference_never_becomes_failure(self):
        r = self.run_classify([row("ascii"), row("chinese", text="other")])
        self.assertEqual((r["status"], r["finding"]), ("INCONCLUSIVE", "OUTPUT_DIFFERENCE"))

    def test_decode_error_preserved_as_unknown(self):
        rows = [row("ascii"), row("chinese")]
        rows[1]["stdout"]["decode_error"] = "invalid utf-8"
        self.assertEqual(self.run_classify(rows)["finding"], "DECODE_ERROR")

    def test_repeat_instability_precedes_path_claim(self):
        rows = [row("ascii"), row("chinese", 7), row("ascii", repeat=2), row("chinese", repeat=2)]
        self.assertEqual(self.run_classify(rows)["finding"], "UNSTABLE_REPEATS")

    def test_success_and_opt_in_exact_cwd_normalization(self):
        rows = [row("ascii", text="C:\\x"), row("chinese", text="C:\\中文")]
        rows[1]["cwd"] = "C:\\中文"
        self.assertEqual(self.run_classify(rows)["status"], "INCONCLUSIVE")
        self.assertEqual(self.run_classify(rows, True)["status"], "PASS")
        self.assertEqual(rows[1]["stdout"]["text"], "C:\\中文")


if __name__ == "__main__":
    unittest.main()
