# Product validation — 2026-10-28

Decision: **bounded GO for a local MVP**, not evidence of adoption or market size.
Research used public repository issues and primary technical documentation. No
third-party affected application was installed or executed. Search results are
not exhaustive; absence of a direct competitor is not proof of uniqueness.

## Alternatives and competition

| Alternative | Already solves | Remaining setup for this use case |
| --- | --- | --- |
| [pytest parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html), [tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html), [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) | Matrix inputs, isolated directories, chdir, environment changes, assertions and CI reporting | Write a harness for arbitrary executables, verify the entire ASCII baseline, capture bounded raw bytes, terminate process trees, classify baseline failures separately. Strongest substitute for existing Python suites. |
| [PowerShell Start-Process](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/start-process?view=powershell-7.5), [.NET ArgumentList](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.processstartinfo.argumentlist) | Launch commands, choose working directory, redirect streams | A small loop is enough for a smoke test. Robust argument handling needs care: Start-Process joins its ArgumentList; .NET ArgumentList performs escaping. Reporting, bounded capture and classification remain custom code. |
| [trycmd](https://docs.rs/trycmd/latest/trycmd/), [snapbox](https://github.com/assert-rs/snapbox) | CLI status/output snapshots, fixtures, precise cwd and binary streams; mature alternatives | Define path cases and Windows root policy; add path-oriented interpretation and lifecycle policy. Prefer these for a Rust project's richer assertion suite. |
| [Prysk](https://github.com/prysk/prysk) / Cram | Language-independent command transcript tests | A general CLI testing substitute; path matrix and diagnostic policy still need authoring. No claim that it cannot run these tests. |
| [GitHub Actions matrix](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations) | Windows runner jobs and parameter combinations | Workflow author must create and inspect paths, execute probes, collect and interpret logs. Complements rather than replaces a local runner. |
| [uni](https://github.com/source-foundry/uni) and filename validators | Inspect Unicode code points / validate names | Different task: no execution-based compatibility evidence. |

Repository and web searches included `unicode path test windows`, `unicode path
tester`, `unicode path test runner`, and `unicode-path test command`. Broad GitHub
connector searches returned noisy results, so concrete tools and documentation
were inspected separately. Stars were not used as a quality or exclusion rule.
No inspected tool documents this exact opinionated workflow as its primary job;
the underlying capabilities already exist in general-purpose frameworks.

## Real faults and limits of evidence

1. **Codex desktop / Electron:** [openai/codex #13553](https://github.com/openai/codex/issues/13553)
   reports startup mkdir failure with a mangled non-ASCII profile path on Windows.
   The reproduction requires a non-ASCII Windows user profile and Store startup.
   The issue is closed; April comments report successful startup on an updated
   version, while a June comment reports another Korean-profile failure. This is
   historical evidence, not a claim that every current version is broken. The
   original encoding diagnosis was the reporter's hypothesis. **Cwd-only MVP
   cannot reproduce that account/profile initialization scenario.** Changing cwd
   or TEMP does not create a different Windows account. Sandbox ACL/TEMP setup
   failures are also outside a child cwd probe's authority.

2. **Node binding / native database:** [alibaba/zvec #665](https://github.com/alibaba/zvec/issues/665)
   reports native process termination at insert for selected collection paths,
   with ASCII controls, repeated measurements and version pinning. A maintainer
   comment says it was reproduced and would be fixed in the next release. The
   issue is closed; a released fix version was not established here. The trigger
   is explicitly unresolved, not simply all non-ASCII names. **An author-supplied
   script using a relative collection path could expose this class of fault**;
   cwdprobe's six samples cannot reproduce or exhaust its full corpus. No zvec
   reproduction was run locally.

3. **Rust GNU / GCC linker:** [rust-lang/cargo #5632](https://github.com/rust-lang/cargo/issues/5632)
   reports Rust 1.26.2 GNU builds failing with non-ASCII project/cache locations.
   Comments compare an accented project directory with an ASCII one; a maintainer
   attributes the limitation to GCC command-line handling rather than Cargo.
   Closed as outside Cargo, **not evidence of a Cargo fix**. This is historical
   toolchain evidence, not a current Rust compatibility claim. Full project/cache
   relocation is needed; an empty-cwd runner with an absolute manifest is
   insufficient. **Not directly reproducible in this MVP.**

4. **Python frozen executable / loader:** [pyinstaller/pyinstaller #1224](https://github.com/pyinstaller/pyinstaller/issues/1224)
   contains a hello-world build and a non-ASCII executable-directory comparison
   across drives. Maintainer analysis discusses narrow versus wide loader APIs
   and short paths; it was closed in 2015 with the Python 3 branch expected to
   fix it. **Historical resolved/expected-fixed issue**, not evidence of a current
   PyInstaller defect. Changing only cwd cannot relocate an executable and its
   DLLs, so this exact reproduction is **outside MVP scope**.

These demonstrate recurring engineering risk in distinct stacks, not customer
interviews, demand volume or willingness to adopt this particular tool. The
local negative sample is deliberately simulated and never presented as one of
these real products failing.

## Why continue, and when not to use it

Target: maintainers shipping Windows CLI programs or native bindings who can
write a tiny trusted smoke command that uses relative files. One command replaces
six manually created working directories, six executions, byte capture, baseline
inspection and a comparison report. Default two repeats means twelve executions.
This is an operation count, not a measured time saving. Existing pytest/trycmd
users may reasonably keep their own tests; the project does not replace them.

Independent value: a reusable, language-independent **cwd experiment protocol**
with fail-closed ASCII-root validation, raw evidence and conservative verdicts.
Not a Unicode-certification scanner and not an automatic root-cause diagnosis.
One person can maintain a small standard-library package with Windows CI; the
Win32 lifecycle adapter is the main maintenance cost. No servers, paid APIs,
plugin system, GUI, project copier, account simulation or repair engine.

Go is conditional on the runner proving its classification and cleanup locally.
If real users require profile/executable relocation before it is useful, revisit
scope or stop; do not expand into a Windows environment manager by default.

## Naming and implementation

Working name **cwdprobe**: exact GitHub `cwdprobe in:name` search returned no
repositories on this date; exact web search found incidental probe-directory
names but no obvious established product. This is not trademark clearance or a
package-name reservation. `Pathweft` was rejected because an existing app uses it.

Python 3.11+ and standard library: existing native interpreter available, mature
Unicode paths/argv, unittest, JSON, hashing and zipapp. Runtime requires Python;
this is a Windows-native CLI, **not a standalone .exe**. PowerShell 7 would also
work but requires more bespoke report/test machinery. Rust could yield a single
binary but would add a build environment and dependencies absent from this host.

Implementation references: [Python subprocess](https://docs.python.org/3.12/library/subprocess.html),
[Windows job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[thread snapshots](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot),
[ResumeThread](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-resumethread).
No third-party implementation source is copied or vendored.
