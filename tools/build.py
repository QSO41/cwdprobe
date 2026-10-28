"""Build a reproducible zipapp using only the standard library."""

import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build():
    files = {p.relative_to(ROOT).as_posix(): p.read_bytes()
             for p in sorted((ROOT / "cwdprobe").glob("*.py"))}
    files["__main__.py"] = b"from cwdprobe.__main__ import main\nraise SystemExit(main())\n"
    files["LICENSE"] = (ROOT / "LICENSE").read_bytes()
    destination = ROOT / "dist" / "cwdprobe.pyz"
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    print("dist/cwdprobe.pyz sha256=" + hashlib.sha256(destination.read_bytes()).hexdigest())
    return destination


if __name__ == "__main__":
    build()
