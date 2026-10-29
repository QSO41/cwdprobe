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

## Quick start from the release

Download **cwdprobe-0.1.0.pyz** and **SHA256SUMS.txt** from
[v0.1.0 Release assets](https://github.com/QSO41/cwdprobe/releases/tag/v0.1.0).
No source ZIP or clone is needed. Open a normal **native Windows PowerShell 7**
terminal in the download folder, with Python 3.11 or 3.12 on PATH.
**The pyz still needs Python; it is not a standalone EXE.** No runtime packages
to install. This is not a WSL/Linux workflow.

### 1. Check Python and the archive

~~~powershell
$pythonExe = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
& $pythonExe --version
& $pythonExe -c "import os, sys; print(os.name, sys.executable)"
$expectedHash = ((Get-Content .\SHA256SUMS.txt -Raw).Trim() -split '\s+')[0]
$actualHash = (Get-FileHash .\cwdprobe-0.1.0.pyz -Algorithm SHA256).Hash
if ($actualHash -ne $expectedHash) { throw 'SHA-256 mismatch; stop here' }
& $pythonExe .\cwdprobe-0.1.0.pyz --version
~~~

Check that the first version is **3.11.x or 3.12.x**, the platform line starts
with **nt** and the archive version is **0.1.0**. Stop if Python is missing or
outside that profile. Hash comparison is case-insensitive; a mismatch stops the
block. The checksum detects mismatched bytes, not publisher identity.

### 2. Prepare the test root

Choose a dedicated folder under an **existing local ASCII parent you own and
can write to**, e.g. `D:\work\cwdprobe-work` if `D:\work` is yours and writable.
Enter its full absolute path below; the block creates it if absent.
`--root` must already exist when cwdprobe starts. Its **entire path**, including
all parents, must use only letters, digits, underscore, dot, hyphen and directory
separators after the drive prefix; no traversal components or reparse ancestors.
An English leaf under a Chinese user profile is not an ASCII baseline.
Do not elevate or switch to TEMP/TMP to bypass this requirement. If no suitable
location is available, stop; that is not evidence your app failed.

~~~powershell
$testRoot = Read-Host 'Full ASCII path for a dedicated test root you own'
if (-not (Test-Path -LiteralPath $testRoot)) {
    New-Item -ItemType Directory -Path $testRoot -ErrorAction Stop | Out-Null
}
~~~

### 3. Run a real external file IO command

This self-contained command uses the installed Python to create/read Chinese,
Japanese, Korean and space filenames in every fresh cwd and check the contents.
It needs neither a source checkout nor an internal demo.
The report parent below is created if needed; **do not create the report leaf**:
cwdprobe creates it. Its parent must exist and the target must be new on every
run. The GUID gives each run a new report name; old reports are never overwritten.

**Trusted commands only: this is not a security sandbox.** Commands inherit your
permissions and environment and can access other files or the network.

~~~powershell
$reportParent = Join-Path (Get-Location).Path 'reports'
if (-not (Test-Path -LiteralPath $reportParent)) {
    New-Item -ItemType Directory -Path $reportParent -ErrorAction Stop | Out-Null
}
$report = Join-Path $reportParent ('io-' + [guid]::NewGuid().ToString('N'))
$code = @'
from pathlib import Path
payload = '中文 / 日本語 / 한국어 / "quoted text"'
for name in ('中文 file.txt', '日本語.txt', '한국어.txt'):
    path = Path(name)
    path.write_text(payload, encoding='utf-8')
    if path.read_text(encoding='utf-8') != payload:
        raise SystemExit('roundtrip mismatch')
print('relative-io-ok')
'@
& $pythonExe .\cwdprobe-0.1.0.pyz --root $testRoot --report $report -- $pythonExe -c $code
$testExit = $LASTEXITCODE
Get-Content (Join-Path $report 'report.txt')
"cwdprobe exit: $testExit"
~~~

Expect `PASS: NO_DIFFERENCE_OBSERVED | 12 executions | cleanup=PASS` and exit 0.
Read the report's first status line, case rows and Cleanup; JSON contains the
raw output and details. This is a constructed safe IO sample, not a third-party
bug reproduction. A PASS covers these sampled paths and this command only.

To test your app, replace everything **after `--`** with its trusted executable
and arguments, e.g. `-- C:\tools\my-app.exe --self-test`. Before `--` are cwdprobe's
options. Keep the new report-name step for every run. Use absolute script/resource
paths; relative data arguments resolve in each initially empty cwd. Prefer an
absolute .exe; a PATH .exe name is resolved once. Batch files need an explicit
interpreter. Arguments use an array and shell=False; code passed to an explicit
shell/interpreter is still your responsibility.

cwdprobe does not scan for apps, upload reports or change permanent system settings.

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

### Optional: recognize an expected failure

Using the variables above, this deliberately simulated command exits 23 only in
non-ASCII cwd paths. It is safe and not a claim about any third-party application.

~~~powershell
$failureReport = Join-Path $reportParent ('expected-failure-' + [guid]::NewGuid().ToString('N'))
$failureCode = 'import os, sys; sys.exit(23 if not os.getcwd().isascii() else 0)'
& $pythonExe .\cwdprobe-0.1.0.pyz --root $testRoot --report $failureReport -- $pythonExe -c $failureCode
$failureExit = $LASTEXITCODE
Get-Content (Join-Path $failureReport 'report.txt')
"cwdprobe exit: $failureExit"
~~~

Expect `FAIL / PATH_SENSITIVE_FAILURE`, exit 1: ASCII/space/symbol cases succeed,
Chinese/Japanese/Korean cases exit 23. This expected FAIL means the probe observed
the simulated failure; it does not mean cwdprobe failed to run.

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

## Feedback

[Open an issue](https://github.com/QSO41/cwdprobe/issues) for a bug, blocked setup,
success case or suggestion. A short description is enough:

1. Windows version/architecture, Python version and cwdprobe version.
2. The test command, with sensitive arguments redacted as needed.
3. Expected vs actual result, including status/finding if available.
4. Which step blocked you.
5. Whether it was easier than your existing script, and why.

Review local paths, command arguments and program output before sharing; remove
private information. Full logs/reports, Stars and public business source code
are not required. Base64 output in JSON is not redacted.

## Source checkout (optional)

From a cloned/extracted source folder, `python -m cwdprobe --version` and
`python -m cwdprobe --help` work without installing runtime packages. Replace
`& $pythonExe .\cwdprobe-0.1.0.pyz` above with `python -m cwdprobe` for source use.
Optional installation into your chosen environment: `python -m pip install .`
(needs setuptools to build). `examples/relative_io.py` is an additional source
example; the release quick start does not depend on it.

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

**Hosted CI: PASS** on Windows Server 2025 x64, CPython 3.11.9 and 3.12.10:
[observed validation run](https://github.com/QSO41/cwdprobe/actions/runs/40728447477).
Both jobs passed all 42 tests, reproducible builds and isolated zipapp smoke tests.
The Windows workflow has read-only default permissions. The CLI does not upload
data; CI archives only synthetic self-test failure logs.
[Validation](docs/VALIDATION.md) · [Release procedure](docs/RELEASING.md).
MIT license; see [LICENSE](LICENSE).
