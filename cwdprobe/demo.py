"""Trusted built-in fixture; also runnable directly with good/ascii-only/always-fail."""

import os
from pathlib import Path
import sys

mode = sys.argv[1]
if mode == "always-fail":
    sys.exit(17)
if mode == "ascii-only" and not os.getcwd().isascii():
    sys.exit(23)
for name in ("sample.txt", "中文.txt", "日本語.txt", "한국어.txt", "a space.txt", "safe&()!.txt"):
    path = Path(name)
    payload = "中文 / 日本語 / 한국어\n".encode("utf-8")
    path.write_bytes(payload)
    if path.read_bytes() != payload:
        sys.exit(19)
os.write(1, b"roundtrip-ok\n")
