"""Controlled Windows startup-interruption and partial-initialization regressions."""

import _thread
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from cwdprobe.experiment import run_experiment
from cwdprobe.process import run_process
from cwdprobe.workspace import Workspace


class R1RegressionTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace(Path(os.environ["CWDPROBE_TEST_ROOT"]))
        self.cwd = self.w.case("ascii", 1)

    def tearDown(self):
        if self.w.path.exists():
            self.w.cleanup()

    def test_sigint_before_popen_returns_cannot_orphan_suspended_child(self):
        original = subprocess.Popen
        created = []

        def interrupted_popen(*args, **kwargs):
            process = original(*args, **kwargs)
            created.append(process)
            _thread.interrupt_main()
            return process

        try:
            with patch("cwdprobe.process.subprocess.Popen", side_effect=interrupted_popen):
                result = run_process([sys.executable, "-c", "open('ran','w').write('bad')"],
                                     self.cwd, 2, 1024, "utf-8")
            self.assertEqual(result["state"], "INTERRUPTED")
            self.assertIsNotNone(created[0].poll(), "suspended child survived cancellation before Popen return")
            self.assertFalse((self.cwd / "ran").exists())
        finally:
            # Exact handles of this test's suspended child only, even on RED.
            for process in created:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=3)
                for pipe in (process.stdout, process.stderr):
                    if pipe and not pipe.closed:
                        pipe.close()

    def test_sigint_after_first_capture_starts_still_returns_report(self):
        original = threading.Thread.start
        starts = []

        def interrupted_start(thread):
            original(thread)
            starts.append(thread)
            if len(starts) == 1:
                _thread.interrupt_main()

        try:
            with patch("cwdprobe.process.threading.Thread.start", new=interrupted_start):
                result = run_process([sys.executable, "-c", "print('ok')"], self.cwd, 2, 1024, "utf-8")
        except RuntimeError as exc:
            self.fail(f"startup SIGINT escaped structured report: {exc}")
        self.assertEqual(result["state"], "INTERRUPTED")
        self.assertTrue(all(not thread.is_alive() for thread in starts))

    def test_failed_capture_start_is_tool_error_without_unstarted_join(self):
        with patch("cwdprobe.process.threading.Thread.start", side_effect=RuntimeError("thread quota")):
            try:
                result = run_process([sys.executable, "-c", "print('ok')"], self.cwd, 2, 1024, "utf-8")
            except RuntimeError as exc:
                self.fail(f"thread startup failure escaped structured report: {exc}")
        self.assertEqual(result["state"], "TOOL_ERROR")

    def test_capture_setup_oserror_never_resumes_user_code(self):
        with patch("cwdprobe.process.Capture", side_effect=OSError("capture resources")):
            result = run_process([sys.executable, "-c", "open('ran','w').write('bad')"],
                                 self.cwd, 2, 1024, "utf-8")
        self.assertEqual(result["state"], "TOOL_ERROR")
        self.assertFalse((self.cwd / "ran").exists())

    def test_sigint_during_workspace_cleanup_finishes_and_reports(self):
        from cwdprobe.winfs import delete_handle
        fired = []

        def interrupted_delete(handle):
            if not fired:
                fired.append(True)
                _thread.interrupt_main()
            return delete_handle(handle)

        try:
            with patch("cwdprobe.winfs.delete_handle", side_effect=interrupted_delete):
                result = run_experiment([sys.executable, "-c", "print('ok')"], self.cwd, repeats=1)
        except KeyboardInterrupt:
            self.fail("cleanup SIGINT escaped before a structured report")
        self.assertEqual(result["summary"]["status"], "INTERRUPTED")
        self.assertEqual(result["cleanup"]["status"], "PASS")
        self.assertFalse(Path(result["workspace"]).exists())

    def test_cleanup_sigint_does_not_hide_prior_launch_error(self):
        from cwdprobe.winfs import delete_handle
        invalid = self.cwd / "invalid.exe"
        invalid.write_bytes(b"not an executable")
        fired = []

        def interrupted_delete(handle):
            if not fired:
                fired.append(True)
                _thread.interrupt_main()
            return delete_handle(handle)

        with patch("cwdprobe.winfs.delete_handle", side_effect=interrupted_delete):
            result = run_experiment([str(invalid)], self.cwd, repeats=1)
        self.assertEqual(result["results"][0]["state"], "LAUNCH_ERROR")
        self.assertEqual(result["summary"]["status"], "TOOL_ERROR")
        self.assertEqual(result["cleanup"]["status"], "PASS")

    def test_partial_marker_write_failure_reports_retained_workspace(self):
        original = Path.open
        allocated = []

        class BrokenWriter:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def write(self, value):
                raise OSError("simulated disk-full after exclusive marker creation")

            def __exit__(self, *args):
                self.stream.close()

        def broken_marker(path, *args, **kwargs):
            stream = original(path, *args, **kwargs)
            if path.name == ".cwdprobe-owner" and args[:1] == ("x",):
                allocated.append(path.parent)
                return BrokenWriter(stream)
            return stream

        try:
            with patch("pathlib.Path.open", new=broken_marker):
                result = run_experiment([sys.executable, "-c", "print('ok')"], self.cwd)
            self.assertEqual(result["summary"]["status"], "TOOL_ERROR")
            self.assertEqual(result["workspace"], str(allocated[0]))
            self.assertEqual(result["cleanup"]["status"], "FAIL")
            self.assertIn("disk-full", result["error"])
        finally:
            # The failed fixture never ran user code; remove only its exact
            # empty marker and directory, with no recursive delete.
            for path in allocated:
                self.assertEqual(path.parent, self.cwd)
                (path / ".cwdprobe-owner").unlink()
                path.rmdir()
