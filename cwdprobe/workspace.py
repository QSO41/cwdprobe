"""Own only new directories; never follow links during cleanup."""

import os
from pathlib import Path
import re
import stat
import uuid

if os.name == "nt":
    from .winfs import drive_type

CASES = {
    "ascii": "English1",
    "chinese": "中文测试目录甲乙",
    "japanese": "日本語テスト甲乙",
    "korean": "한국어테스트갑을",
    "spaces": "a space1",
    "symbols": "safe&()!",
}


def checked_stat(path):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError("Reparse points and symbolic links are refused")
    return info


def validate_chain(path):
    for part in reversed((path, *path.parents)):
        checked_stat(part)


def validate_root(root):
    root = Path(root)
    value = str(root)
    if os.name != "nt":
        raise ValueError("Native Windows is required")
    if not re.fullmatch(r"[A-Za-z]:\\[A-Za-z0-9_.\\-]*", value):
        raise ValueError("Root must be an existing ASCII local-drive absolute path without spaces/symbols")
    if any(p in {".", ".."} for p in value.split("\\")):
        raise ValueError("Root traversal components are refused")
    validate_chain(root)
    if not root.is_dir():
        raise ValueError("Root is not a directory")
    if drive_type(root.anchor) not in {2, 3, 6}:
        raise ValueError("Root must be on a local fixed/removable/RAM drive")
    resolved = root.resolve(strict=True)
    if not re.fullmatch(r"[A-Za-z]:\\[A-Za-z0-9_.\\-]*", str(resolved)):
        raise ValueError("Resolved root is not a plain local ASCII baseline")
    if drive_type(resolved.anchor) not in {2, 3, 6}:
        raise ValueError("Resolved root is not on a local drive")
    validate_chain(resolved)
    return resolved


class Workspace:
    def __init__(self, root):
        self.root = validate_root(root)
        self.token = uuid.uuid4().hex
        self.path = self.root / ("cwdprobe-" + self.token)
        self.path.mkdir()
        self.identity = (self.path.stat().st_dev, self.path.stat().st_ino)
        try:
            with (self.path / ".cwdprobe-owner").open("x", encoding="ascii") as f:
                f.write(self.token)
        except BaseException:
            # Only this empty directory was created; no recursive deletion.
            self.path.rmdir()
            raise

    def verify(self):
        validate_chain(self.path)
        info = checked_stat(self.path)
        if (info.st_dev, info.st_ino) != self.identity or self.path.parent != self.root:
            raise ValueError("Owned run directory was replaced")
        marker = self.path / ".cwdprobe-owner"
        if checked_stat(marker).st_nlink != 1 or marker.read_text(encoding="ascii") != self.token:
            raise ValueError("Owned run marker does not match")

    def case(self, name, repeat):
        self.verify()
        leaf = CASES[name]
        path = self.path / f"r{repeat:02d}" / leaf
        path.parent.mkdir(exist_ok=True)
        checked_stat(path.parent)
        path.mkdir()
        return path

    def cleanup(self):
        from .winfs import safe_cleanup
        safe_cleanup(self)
