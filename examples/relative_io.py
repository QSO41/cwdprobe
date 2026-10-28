"""Standalone smoke test for use after -- ABSOLUTE_PYTHON ABSOLUTE_SCRIPT."""

from pathlib import Path
import os

payload = "中文 / 日本語 / 한국어".encode("utf-8")
for name in ("中文.txt", "日本語.txt", "한국어.txt", "with space.txt"):
    path = Path(name)
    path.write_bytes(payload)
    assert path.read_bytes() == payload, f"Roundtrip failed: {name}"
os.write(1, b"relative-io-ok\n")
