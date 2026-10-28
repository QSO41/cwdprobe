# cwdprobe

**Check whether a trusted Windows command behaves differently under different
working-directory names.** Run one command in an ASCII control plus Chinese,
Japanese, Korean, space and valid punctuation directories, with two fresh runs
per case by default. Read the local text/JSON report.

[简体中文](README.zh-CN.md) · [v0.1.0 notes](docs/releases/v0.1.0.md) · [Report format](docs/REPORT.md)

Useful for CLI smoke tests that open relative files. It saves writing the matrix,
Windows process-tree handling, bounded byte capture and comparison report.
An existing pytest or PowerShell suite may already meet your needs.

**Verified v0.1.0 profile: Windows 11 x64, native CPython 3.11 or 3.12.**
Windows 10, ARM64, Python 3.13 and later are **NOT TESTED**. The package metadata's
Python 3.11 minimum is not a broader support guarantee.

## Run without installing

From a source checkout/extracted source folder, open a normal PowerShell 7
terminal with a verified native Python on PATH. No runtime packages to install.

~~~powershell
python --version
python -m cwdprobe --version
python -m cwdprobe --help
~~~

Alternatively, use the release archive:

~~~powershell
python .\cwdprobe-0.1.0.pyz --version
python .\cwdprobe-0.1.0.pyz --help
Get-FileHash .\cwdprobe-0.1.0.pyz -Algorithm SHA256
~~~

Compare the hash with SHA256SUMS.txt. **The pyz still requires a supported native
Windows Python interpreter. It is not a standalone EXE.** For archive use, replace
"python -m cwdprobe" below with "python .\cwdprobe-0.1.0.pyz"; no checkout is needed.
Optional source installation into your chosen environment: "python -m pip install ."
(needs setuptools to build).

## First real command

Choose a writable local **ASCII-only root you own**; edit the example if needed.
The full path must contain only letters, digits, underscore, dot, hyphen and
directory separators, with no reparse ancestors. An English folder below a
Chinese user profile is not an ASCII control. Do not elevate to obtain access.

~~~powershell
$testRoot = 'C:\cwdprobe-work' # choose your own writable ASCII location
New-Item -ItemType Directory -Path $testRoot # skip if it already exists
New-Item -ItemType Directory -Path .\reports -Force | Out-Null
$pythonExe = (Get-Command python).Source
python -m cwdprobe --root $testRoot --report reports\python-version -- $pythonExe --version
Get-Content .\reports\python-version\report.txt
~~~

This executes the actual installed Python twelve times, not an internal demo.
Use a **new report directory name every time**. Its parent must exist; existing
report directories are never overwritten.

From a source checkout, use the standalone relative-file IO test:

~~~powershell
$probeScript = (Resolve-Path .\examples\relative_io.py).Path
python -m cwdprobe --root $testRoot --report reports\relative-io -- $pythonExe $probeScript
~~~

It writes/reads multilingual and space filenames and asserts their contents.
To test your app, replace everything after "--" with its trusted executable and
arguments, e.g. "-- C:\tools\my-app.exe --self-test". Use absolute script/resource
paths; relative data arguments resolve in each initially empty cwd. Prefer an
absolute .exe; a PATH .exe name is resolved once. Batch files need an explicit
interpreter. Arguments use an array and shell=False; code passed to an explicit
shell/interpreter is still your responsibility.

**Trusted commands only: this is not a security sandbox.** Commands inherit your
permissions and environment and can access other files or the network. cwdprobe
does not scan for apps, upload reports or change permanent system settings.

## Read the result

| Status / finding | Meaning | Exit |
| --- | --- | --- |
| PASS / NO_DIFFERENCE_OBSERVED | All samples exit 0 with stable comparable output | 0 |
| FAIL / PATH_SENSITIVE_FAILURE | ASCII succeeds; a variant consistently exits nonzero | 1 |
| FAIL / GENERAL_FAILURE | Every sample consistently exits nonzero | 1 |
| INCONCLUSIVE / BASELINE_FAILURE | ASCII fails but another case succeeds | 3 |
| INCONCLUSIVE | Timeout, output cap, decoding, unstable repeats or output differences | 3 |
| TOOL_ERROR | Setup, launch, capture, cleanup or report could not complete | 2 |
| INTERRUPTED | Ctrl+C/KeyboardInterrupt, with cleanup where possible | 130 |

Path sensitivity **does not establish a Unicode encoding root cause**. Exit 0
needs an app-specific smoke test to assert functional correctness. Plain output
differences are not program failures. Optional --normalize-cwd substitutes only
the exact cwd for cross-case text comparison, preserving raw evidence. Repeat
stability always ignores that known exact cwd change between fresh runs.

report.txt is the summary. report.json contains resolved argv, EXE SHA-256,
settings, OS/codepage context, paths/codepoints, states, timings, raw stdout/stderr
prefixes, hashes and strict decoding diagnostics. Scripts/dependencies/full
environment are not snapshotted. Review reports before sharing: paths, arguments
and output may be private; base64 is not redaction.

Options: --repeats 1..10 (default 2), --timeout seconds (default 10),
--max-bytes per stream/run (default 1 MiB, maximum 16 MiB), --encoding utf-8,
--normalize-cwd. See --help. Encoding changes decoding only, not the child locale.
High limits/repeats increase report memory. The timeout cannot preempt a blocked
Windows CreateProcess or the EXE hashing before execution.

## Cleanup and troubleshooting

Normal completion removes only its new owned cwdprobe-<id> directory. The chosen
root and reports remain; review/delete your selected reports yourself. Job Objects
end remaining descendants on timeout, output cap and parent exit. Ctrl+C is
deferred during short ownership transitions, then reported safely. Force-kill,
power loss or unsafe/locked contents can leave directories. There is no old-run
cleanup command or automatic deletion of stale runs.

| Symptom | Next step |
| --- | --- |
| Root / SETUP_ERROR | Check the full root is existing, ASCII, local and writable; choose another owned location without elevating. |
| Report directory error | Create its parent and choose a new leaf; no new report is written when directory setup fails. |
| LAUNCH_ERROR / EXECUTION_ERROR | Read the row's error in JSON; verify absolute EXE/script paths and interpreter. |
| DECODE_ERROR | Check the producer's actual codec, inspect raw bytes, then select e.g. --encoding gbk if appropriate. |
| TIMEOUT / OUTPUT_LIMIT | Review the trusted command, then adjust its limit if needed; this is inconclusive, not a Unicode diagnosis. |
| CLEANUP_ERROR / partial owner setup | Inspect the exact workspace, close only your own handles and review contents/links before manual removal. Never delete the selected root or unrelated directories. |

Cleanup uses verified Windows handles and refuses reparse points, hard links,
replaced ownership and special files. Partial owner setup is retained with cleanup
FAIL and its original error. Do not modify an active run tree concurrently.

## Scope, development and CI

Only cwd variation is implemented: no account/profile simulation, TEMP/TMP matrix,
codepage changes, executable/project relocation, fixture copying, long-path
certification, interactive/GUI support or repair. WSL/Linux is not Windows
verification. Real third-party bug reproductions remain NOT TESTED.

~~~powershell
$env:CWDPROBE_TEST_ROOT = $testRoot # dedicated test root, not a shared work folder
python -m unittest discover -s tests -v
python tools\check.py
python tools\build.py
~~~

The 42 meaningful tests cover lifecycle, arguments, IO, diagnosis, classification
and cleanup. Some tests deny/restore permissions or create/remove junctions only
on their own fixtures. No administrator or third-party test packages needed.
The build creates deterministic dist/cwdprobe.pyz; it still needs Python.

Windows Actions is prepared for Python 3.11/3.12, read-only default permissions
and self-test failure logs. **Hosted CI: NOT TESTED** until run on GitHub. The CLI
does not upload data; CI archives only synthetic self-test failure logs. No CI
badge is claimed. [Validation](docs/VALIDATION.md) · [Release procedure](docs/RELEASING.md).
MIT license; see [LICENSE](LICENSE).
