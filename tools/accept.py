"""Local-only, self-fixture acceptance with saved logs and sample reports."""

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("Native Windows required")
    if ctypes.windll.shell32.IsUserAnAdmin():
        parser.error("Use a normal non-administrator terminal for local acceptance")
    output = ROOT / "local-acceptance" / ("run-" + uuid.uuid4().hex[:12])
    output.mkdir(parents=True)
    env = os.environ.copy()
    env["CWDPROBE_TEST_ROOT"] = str(args.root)

    def run(name, command, expected=0):
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=120)
        (output / (name + ".stdout.bin")).write_bytes(process.stdout)
        (output / (name + ".stderr.bin")).write_bytes(process.stderr)
        (output / (name + ".txt")).write_text(
            process.stdout.decode("utf-8", errors="backslashreplace") +
            process.stderr.decode("utf-8", errors="backslashreplace"), encoding="utf-8")
        if process.returncode != expected:
            raise RuntimeError(f"{name}: expected {expected}, got {process.returncode}; see {output}")

    run("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    run("quality", [sys.executable, "tools/check.py"])
    hashes = []
    for i in range(2):
        run(f"build-{i + 1}", [sys.executable, "tools/build.py"])
        hashes.append(hashlib.sha256((ROOT / "dist/cwdprobe.pyz").read_bytes()).hexdigest())
    if hashes[0] != hashes[1]:
        raise RuntimeError("Reproducible build hashes differ")
    samples = []
    for name, mode, code in [("good", "good", 0), ("path-failure", "ascii-only", 1),
                              ("general-failure", "always-fail", 1)]:
        run(name, [sys.executable, "-m", "cwdprobe", "--root", str(args.root),
                   "--report", str(output / name), "--demo", mode], expected=code)
        report = json.loads((output / name / "report.json").read_text(encoding="utf-8"))
        samples.append({"sample": name, "summary": report["summary"],
                        "executions": len(report["results"]), "cleanup": report["cleanup"]})
    run("zipapp", [sys.executable, "dist/cwdprobe.pyz", "--root", str(args.root),
                   "--report", str(output / "zipapp"), "--demo", "good"])
    manifest = {"completed_utc": datetime.now(timezone.utc).isoformat(),
                "native_os": platform.platform(), "python": platform.python_version(),
                "administrator": False, "tests": "PASS", "quality": "PASS",
                "reproducible_zipapp": "PASS", "zipapp_sha256": hashes[0],
                "zipapp_smoke": "PASS", "samples": samples,
                "not_tested": ["Other Windows/Python versions", "Hosted CI", "Real affected third-party apps",
                               "Physical terminal Ctrl+C", "Account/profile/TEMP relocation"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("Local evidence directory: " + ascii(str(output)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
