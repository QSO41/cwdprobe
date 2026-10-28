# cwdprobe

Run a trusted Windows command in six fresh working-directory paths and keep a
local, conservative compatibility report. Python 3.11+; no runtime dependencies.
Local release candidate, not yet published. Python/Node external smoke commands
have been checked; reproductions of real third-party bugs remain unverified.

[简体中文](README.zh-CN.md) · [Product research](docs/RESEARCH.md) · [Report contract](docs/REPORT.md)

[R1 quality review (中文)](docs/R1_QUALITY_REVIEW.zh-CN.md)

Useful for a CLI smoke command that opens relative files. It automates an ASCII
control, Chinese/Japanese/Korean, spaces and valid ASCII punctuation. This is a
small experiment runner, not comprehensive Unicode certification.

## Quick start (PowerShell 7)

Use a normal, non-administrator Windows terminal. From this checkout:

```powershell
python --version  # Python 3.11 or newer, native Windows
New-Item -ItemType Directory -Path C:\cwdprobe-work  # choose a NEW writable ASCII location
New-Item -ItemType Directory -Path reports
python -m cwdprobe --root C:\cwdprobe-work --report reports\good --demo good
python -m cwdprobe --root C:\cwdprobe-work --report reports\bad --demo ascii-only
```

The first fixture creates and reads multilingual filenames in all six cwd cases,
twice. The second is deliberately broken: it exits 23 only under non-ASCII cwd.
Expected summaries: `PASS / NO_DIFFERENCE_OBSERVED` and
`FAIL / PATH_SENSITIVE_FAILURE`. Reusing a report directory is refused; pick a new
name for each run. If creating a drive-root directory is not permitted, choose an
existing writable ASCII root or create one under an ASCII location you own.
Never solve this by elevating the test.

## Test your command

Only run software you trust. **This is not a security sandbox.** A command has
your permissions and inherited environment; it can change files outside the
test directories, make network requests or run other programs. cwdprobe itself
does not upload reports or scan for programs.

```powershell
python -m cwdprobe --root C:\cwdprobe-work --report reports\my-app --timeout 10 -- C:\tools\my-app.exe --self-test
```

An absolute `.exe` path is preferred. An executable name on an absolute PATH
entry is resolved once; the same resolved executable is used in every case.
Pass script interpreters explicitly, e.g. `-- C:\Python312\python.exe C:\my-tests\probe.py`.
Use absolute paths for the script and fixed resources. Relative data arguments
are relative to each new cwd; the directories start empty. Batch files are
refused. The tool passes an argument array with `shell=False`; it does not parse
a shell command string or automatically escape an explicit interpreter's code.
Programs with custom nonstandard Windows command-line parsers may differ from
the standard C-runtime argument rules.

A copyable external-command example using the included standalone IO script:

```powershell
$pythonExe = (Get-Command python).Source
$probeScript = (Resolve-Path .\examples\relative_io.py).Path
python -m cwdprobe --root C:\cwdprobe-work --report reports\relative-io -- $pythonExe $probeScript
```

Options: `--repeats 1..10` (default 2), `--timeout` (default 10 seconds per case),
`--max-bytes` (default 1 MiB per stream; maximum 16 MiB), `--encoding utf-8`
(or the actual expected text codec, e.g. `gbk`), `--normalize-cwd` (optional exact
cwd substitution during text comparison, keeping original text/bytes).
The encoding option changes decoding only; it does not change a child's locale.

## Interpret a report

| Status / finding | Meaning | CLI code |
| --- | --- | --- |
| PASS / NO_DIFFERENCE_OBSERVED | Every sample completed with exit 0 and stable comparable output | 0 |
| FAIL / PATH_SENSITIVE_FAILURE | ASCII succeeded; a variant returned nonzero consistently | 1 |
| FAIL / GENERAL_FAILURE | All samples returned nonzero consistently | 1 |
| INCONCLUSIVE / BASELINE_FAILURE | ASCII failed but some other samples succeeded | 3 |
| INCONCLUSIVE | Timeout, output cap, decode failure, changing repeats or output differences | 3 |
| TOOL_ERROR | Setup, launch, capture, containment, cleanup or report problem | 2 |
| INTERRUPTED | KeyboardInterrupt, followed by cleanup where possible | 130 |

An observed path-sensitive exit failure is **not a diagnosis of Unicode
causality**. Exit 0 does not prove correct application behavior: your command
must assert the behavior you care about. Plain output differences are never
automatically failures. With fresh repeat directories, the exact cwd is ignored
only when detecting repeat instability; cross-case comparison normalizes it
only when `--normalize-cwd` is requested. No timestamps/random IDs are erased.

`report.txt` contains the readable table; `report.json` contains full argv,
settings, context, exact cwd/codepoints, states, exit codes, timings, raw captured
byte prefixes (base64), hashes and strict decoding errors. Review reports before
sharing: paths, arguments and child output may contain private data. `reports/`
and `local-acceptance/` are ignored by Git. Reports are not auto-uploaded.

## Boundaries and cleanup

The complete test root must be an existing ASCII local-drive absolute path with
letters/digits/underscore/dot/hyphen/separators only, and no reparse ancestors.
An English leaf inside a Chinese user profile is rejected as an ASCII control.
All test work lives inside a new random `cwdprobe-<id>` child. The selected root
itself is never deleted. Equal-length case leaves reduce one length confound but
do not make this a controlled proof of a character-only cause.

Children start suspended, enter a kill-on-close Windows Job Object, then resume.
Containment setup failure stops the child before user code runs. Timeout, output
limit and normal completion close the job, ending remaining descendants. Programs
that intentionally spawn persistent services are unsuitable for this runner.
This is lifecycle containment, not a security boundary or disk/CPU/memory quota.
The timeout accounts for child startup, but cannot preempt a blocked Windows
CreateProcess call or the executable hashing that precedes execution.

Cleanup verifies a per-run ownership marker and directory identity. It inventories
without following links, locks ancestors against rename/write opens, deletes
through verified Windows handles, refuses reparse points/hard links/special files, and
retains unsafe or locked output with a TOOL_ERROR. Do not modify a run tree from
another process during execution. It is not designed to resist malicious
concurrent filesystem races. Ctrl+C normally triggers cleanup; force-killing the
runner or power loss can leave files. There is no automatic stale-tree deletion.
During short startup and cleanup ownership transitions, Ctrl+C is deferred until
resources can be handled safely, then reported as interruption. A partial
ownership-marker initialization is retained with its exact workspace path,
TOOL_ERROR and cleanup FAIL; it is not silently claimed to have been removed.

Not supported: TEMP/TMP variation, new Windows accounts, profile/registry/ACL
simulation, executable/project relocation, fixture copying, interactive/GUI apps,
UNC/device paths, long-path validation or repair. Native Windows execution only;
WSL/Linux results are not Windows verification. The parent environment, Python
installation and external dependencies are not relocated or fully snapshotted.

## Development and reproducible portable archive

```powershell
$env:CWDPROBE_TEST_ROOT = 'C:\cwdprobe-work'
python -m unittest discover -s tests -v
python tools\check.py
python tools\build.py
python dist\cwdprobe.pyz --root C:\cwdprobe-work --report reports\archive --demo good
```

The test root must be dedicated to these tests. Tests launch only self-written
Python fixtures; one test denies then restores create permissions on its own
ephemeral directory, and another creates/removes its own junction. No admin,
third-party test dependencies, network access or system configuration changes.

`build.py` produces a deterministic ZIP application with fixed timestamps and
sorted source entries. It needs the Python runtime; it is not a standalone exe.
Build twice and compare SHA-256. Alternatively, `python -m pip install .` installs
the CLI in your chosen environment (optional; setuptools is needed for packaging).
Source and zipapp use only the standard library, so no installation is necessary.

The included Windows GitHub Actions workflow is ready for a future repository;
hosted CI is **NOT TESTED** until it actually runs. Local acceptance is Windows 11
x64 / Python 3.11 and 3.12; other supported versions remain unverified. See
[validation](docs/VALIDATION.md). MIT license.

For a complete local evidence bundle (tests, two builds and sample reports), run
`python tools/accept.py --root C:\cwdprobe-work` in a non-administrator terminal.
Each invocation creates a new ignored `local-acceptance/run-<id>` directory.
