"""Console interface; report output is always a new local directory."""

import argparse
import codecs
import importlib.resources
import json
import math
import os
from pathlib import Path
import sys

from . import __version__
from .workspace import validate_chain

EXIT_CODES = {"PASS": 0, "FAIL": 1, "TOOL_ERROR": 2, "INCONCLUSIVE": 3, "INTERRUPTED": 130}


def render_text(report):
    summary = report["summary"]
    lines = [f"cwdprobe {report['version']} | {summary['status']} | {summary['finding']}",
             "Scope: cwd-only. Path sensitivity is not a Unicode root-cause diagnosis.",
             "Only run commands you trust. This tool is NOT a security sandbox.",
             f"Command argv: {json.dumps(report['command'], ensure_ascii=True)}",
             f"Settings: {json.dumps(report['settings'], ensure_ascii=True)}", "",
             "case       repeat  state          exit    seconds  decode-errors"]
    for row in report["results"]:
        errors = sum(bool(row[s]["decode_error"]) for s in ("stdout", "stderr"))
        lines.append(f"{row['case']:<10} {row['repeat']:>6}  {row['state']:<14} "
                     f"{str(row['exit_code']):>6} {row['elapsed_seconds']:>10.4f}  {errors}")
    lines.extend(["", f"Cleanup: {report['cleanup']['status']}",
                  "Raw stream bytes, hashes, cwd paths and diagnostics are in report.json.",
                  "Do not publish reports without reviewing paths, argv and output for private data."])
    if report.get("error"):
        lines.append(f"Tool error: {ascii(report['error'])}")
    if report["cleanup"].get("error"):
        lines.append(f"Cleanup error: {ascii(report['cleanup']['error'])}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Test a trusted .exe command under six Windows cwd paths. NOT a sandbox.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--root", type=Path, required=True, help="Existing local ASCII root, no spaces/symbols")
    parser.add_argument("--report", type=Path, required=True, help="New local report directory (never overwritten)")
    parser.add_argument("--demo", choices=["good", "ascii-only", "always-fail"], help="Run a built-in trusted fixture")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=10.0, help="Seconds per child, including setup")
    parser.add_argument("--max-bytes", type=int, default=1048576, help="Capture limit per stream per child")
    parser.add_argument("--encoding", default="utf-8", help="Expected output encoding; raw bytes always retained")
    parser.add_argument("--normalize-cwd", action="store_true", help="Compare text with exact cwd replaced; raw data kept")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- EXE ARG ... (literal argv)")
    args = parser.parse_args(argv)
    if os.name != "nt":
        parser.error("Native Windows required; Linux/WSL is not Windows acceptance")
    if not 1 <= args.repeats <= 10 or not math.isfinite(args.timeout) or not 0 < args.timeout <= 3600:
        parser.error("repeats must be 1..10 and timeout must be finite, >0 and <=3600")
    if not 1 <= args.max_bytes <= 16 * 1024 * 1024:
        parser.error("max-bytes must be 1..16777216")
    try:
        codecs.lookup(args.encoding)
        b"".decode(args.encoding)  # exclude non-text codecs
    except (LookupError, TypeError, UnicodeError) as exc:
        parser.error(str(exc))
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if bool(args.demo) == bool(command):
        parser.error("Choose exactly one: --demo MODE or -- EXE ARG ...")
    if args.demo:
        source = importlib.resources.files("cwdprobe").joinpath("demo.py").read_text(encoding="utf-8")
        command = [sys.executable, "-c", source, args.demo]
    destination = Path(os.path.abspath(args.report))
    try:
        from .winfs import drive_type
        if len(destination.drive) != 2 or drive_type(destination.anchor) not in {2, 3, 6}:
            raise ValueError("Report directory must be on a local drive")
        validate_chain(destination.parent)
        destination.mkdir()  # no parents, no exist_ok, never claim existing content
        validate_chain(destination)
    except (OSError, ValueError) as exc:
        print(f"TOOL_ERROR: cannot create new report directory: {ascii(str(exc))}", file=sys.stderr)
        return 2
    from .experiment import run_experiment
    print("Running a trusted command; this is NOT a sandbox. Reports stay local.", flush=True)
    report = run_experiment(command, args.root, args.repeats, args.timeout,
                            args.max_bytes, args.encoding, args.normalize_cwd)
    try:
        with (destination / "report.json").open("x", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=True, indent=2, allow_nan=False)
            f.write("\n")
        with (destination / "report.txt").open("x", encoding="utf-8", newline="\n") as f:
            f.write(render_text(report))
    except (OSError, ValueError) as exc:
        print(f"TOOL_ERROR: report write failed: {ascii(str(exc))}", file=sys.stderr)
        return 2
    summary = report["summary"]
    print(f"{summary['status']}: {summary['finding']} | {len(report['results'])} executions | "
          f"cleanup={report['cleanup']['status']}")
    print(f"Report: {ascii(str(destination / 'report.json'))}")
    return EXIT_CODES[summary["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
