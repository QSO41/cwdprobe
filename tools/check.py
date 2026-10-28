"""Dependency-free syntax, whitespace and metadata checks."""

import ast
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main():
    problems = []
    files = []
    for folder in ("cwdprobe", "tests", "tools", "examples", "docs", ".github"):
        files.extend(p for p in (ROOT / folder).rglob("*")
                     if p.is_file() and p.suffix in {".py", ".md", ".yml"})
    files.extend(ROOT / name for name in ("README.md", "README.zh-CN.md", "pyproject.toml", "LICENSE"))
    for path in sorted(files):
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            problems.append(f"{path.relative_to(ROOT)}: missing final newline")
        for line_number, line in enumerate(text.splitlines(), 1):
            if line.rstrip() != line or "\t" in line:
                problems.append(f"{path.relative_to(ROOT)}:{line_number}: whitespace")
        if path.suffix == ".py":
            try:
                ast.parse(text, filename=str(path), feature_version=(3, 11))
            except SyntaxError as exc:
                problems.append(str(exc))
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version_ns = {}
    exec((ROOT / "cwdprobe/__init__.py").read_text(encoding="utf-8"), version_ns)
    if metadata["project"]["version"] != version_ns["__version__"]:
        problems.append("package version differs from project metadata")
    if metadata["project"]["dependencies"]:
        problems.append("MVP unexpectedly added runtime dependencies")
    for problem in problems:
        print(problem)
    print(f"Checked {len(files)} source/document files; {len(problems)} problems")
    return bool(problems)


if __name__ == "__main__":
    sys.exit(main())
