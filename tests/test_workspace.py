import os
from pathlib import Path
import unittest

try:
    from cwdprobe.workspace import Workspace, validate_root
except ImportError:
    Workspace = validate_root = None


class WorkspaceTests(unittest.TestCase):
    def test_unicode_parent_is_not_ascii_baseline(self):
        self.assertTrue(callable(validate_root), "root policy is not implemented")
        with self.assertRaises(ValueError):
            validate_root(Path("C:/Users/中文/english"))

    def test_unsafe_root_forms_refused(self):
        self.assertTrue(callable(validate_root), "root policy is not implemented")
        for value in ["relative", "C:relative", "//server/share", "C:/with space", "C:/a&b"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_root(Path(value))

    def test_owned_cleanup_and_foreign_marker(self):
        self.assertTrue(callable(Workspace), "owned workspace is not implemented")
        root = os.environ.get("CWDPROBE_TEST_ROOT")
        self.assertTrue(root, "set CWDPROBE_TEST_ROOT to a dedicated ASCII directory")
        w = Workspace(Path(root))
        path = w.path
        sentinel = path.parent / (path.name + "-protected")
        sentinel.write_text("keep", encoding="ascii")
        try:
            (w.case("chinese", 1) / "sample").write_text("ok", encoding="ascii")
            w.cleanup()
            self.assertFalse(path.exists())
            self.assertEqual(sentinel.read_text(), "keep")
        finally:
            sentinel.unlink(missing_ok=True)
        w = Workspace(Path(root))
        marker = w.path / ".cwdprobe-owner"
        marker.write_text("foreign", encoding="ascii")
        with self.assertRaises(ValueError):
            w.cleanup()
        self.assertTrue(w.path.exists())
        marker.write_text(w.token, encoding="ascii")
        w.cleanup()
