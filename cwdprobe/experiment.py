"""One command, fresh cwd cases, explicit experiment provenance."""

import ctypes
from datetime import datetime, timezone
import hashlib
import locale
import os
from pathlib import Path
import platform
import sys

from . import __version__
from .analysis import classify
from .workspace import CASES, Workspace, checked_stat


def resolve_command(command):
    if not command or not command[0]:
        raise ValueError("A trusted executable command is required")
    value = command[0]
    if Path(value).is_absolute():
        exe = Path(value).resolve(strict=True)
    elif Path(value).name != value or ":" in value:
        raise ValueError("Use an absolute executable path or a PATH executable name")
    else:
        # PATH-only lookup: never discover an executable in a generated test cwd.
        found = None
        for directory in os.get_exec_path():
            if not directory or not Path(directory).is_absolute():
                continue
            candidate = Path(directory) / value
            if candidate.suffix.lower() == ".exe" and candidate.is_file():
                found = candidate
                break
            if not candidate.suffix and candidate.with_suffix(".exe").is_file():
                found = candidate.with_suffix(".exe")
                break
        if not found:
            raise ValueError("Executable not found on absolute PATH entries; prefer its absolute .exe path")
        exe = found.resolve(strict=True)
    checked_stat(exe)
    if exe.suffix.lower() != ".exe" or not exe.is_file():
        raise ValueError("Only .exe commands are supported; pass an interpreter explicitly for scripts")
    return [str(exe), *command[1:]]


def run_experiment(command, root, repeats=2, timeout=10.0, max_bytes=1048576,
                   encoding="utf-8", normalize_cwd=False):
    from .process import run_process

    report = {
        "schema_version": 1, "tool": "cwdprobe", "version": __version__,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "cwd-only", "command": list(command), "results": [],
        "settings": {"repeats": repeats, "timeout_seconds": timeout,
                     "max_bytes_per_stream": max_bytes, "encoding": encoding,
                     "normalize_cwd": normalize_cwd, "environment_overrides": {}},
        "context": {"os": platform.platform(), "python": platform.python_version(),
                    "architecture": platform.machine(),
                    "preferred_encoding": locale.getpreferredencoding(False),
                    "filesystem_encoding": sys.getfilesystemencoding(),
                    "ansi_codepage": ctypes.windll.kernel32.GetACP(),
                    "oem_codepage": ctypes.windll.kernel32.GetOEMCP(),
                    "console_output_codepage": ctypes.windll.kernel32.GetConsoleOutputCP()},
        "cleanup": {"status": "NOT_NEEDED"}, "workspace": None,
        "limitations": ["Trusted commands only; not a sandbox",
                        "cwd-only; no profile, executable relocation, TEMP or codepage simulation",
                        "Six fixed samples; path sensitivity does not establish Unicode causality",
                        "Inherited environment/dependencies may affect reproducibility"],
    }
    workspace = None
    try:
        command = resolve_command(command)
        report["command"] = command
        with open(command[0], "rb") as f:
            report["executable_sha256"] = hashlib.file_digest(f, "sha256").hexdigest()
        workspace = Workspace(root)
        report["workspace"] = str(workspace.path)
        for repeat in range(1, repeats + 1):
            for case, leaf in CASES.items():
                cwd = workspace.case(case, repeat)
                row = run_process(command, cwd, timeout, max_bytes, encoding)
                row.update({"case": case, "repeat": repeat, "cwd": str(cwd),
                            "path_ascii": str(cwd).isascii(), "path_length": len(str(cwd)),
                            "leaf_codepoints": [f"U+{ord(c):04X}" for c in leaf]})
                report["results"].append(row)
                if row["state"] in {"TOOL_ERROR", "LAUNCH_ERROR", "INTERRUPTED"}:
                    return report
    except KeyboardInterrupt:
        report["summary"] = {"status": "INTERRUPTED", "finding": "INTERRUPTED"}
    except (OSError, ValueError) as exc:
        report["summary"] = {"status": "TOOL_ERROR", "finding": "SETUP_ERROR"}
        report["error"] = str(exc)
    finally:
        if "summary" not in report:
            report["summary"] = classify(report["results"], normalize_cwd)
        if workspace:
            try:
                workspace.cleanup()
                report["cleanup"] = {"status": "PASS"}
            except (OSError, ValueError) as exc:
                report["cleanup"] = {"status": "FAIL", "error": str(exc)}
                report["summary"] = {"status": "TOOL_ERROR", "finding": "CLEANUP_ERROR"}
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    return report
