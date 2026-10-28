# Local MVP acceptance — 2026-10-28

**GO delivered for local human review. No remote repository, release or upload.**

Native Windows 11 x64, build 26200; Python 3.11.15 and 3.12.14; PowerShell 7.6.5;
non-administrator token. Source standard library only. Local project version 0.1.0.

| Check | Status | Actual result |
| --- | --- | --- |
| Automatic suite | PASS | 35 tests on each of the two Python versions; no failures/errors/skips |
| Syntax/whitespace/metadata | PASS | Final 29 files checked, no problems |
| Good IO command | PASS | 6 cases x 2 repeats; all exit 0; exact `roundtrip-ok` output |
| Simulated non-ASCII-only fault | FAIL (expected) | ASCII/spaces/symbols exit 0; Chinese/Japanese/Korean exit 23 on both repeats; PATH_SENSITIVE_FAILURE |
| Simulated universal fault | FAIL (expected) | All 12 exit 17; GENERAL_FAILURE |
| Workspace cleanup | PASS | All sample run directories removed; dedicated root retained and empty |
| Reproducible zipapp | PASS | Two builds have the same SHA-256 below |
| Zipapp real smoke | PASS | 12 good-case executions, clean exit and cleanup |
| Independent core review | PASS after fixes | Three findings fixed and regression-tested; follow-up found no blocking defect |

Zipapp SHA-256:
`0f2927513b9b6077583e089b66297c286272c684560dba1950a6c8944c59b0a4`

Machine-specific JSON reports, test logs and manifest are stored under the
ignored `local-acceptance/run-360f91ba3590/` directory. `good/report.json`,
`path-failure/report.json`, `general-failure/report.json`, and `zipapp/report.json`
retain exact argv, paths, bytes and context. They are intentionally excluded from
the source commit. This sanitized document does not replace that raw evidence.
The native Python 3.11 repeat is stored in `local-acceptance/run-84afcf8c17f8/`;
all three sample outcomes and the zipapp smoke also pass there, with the same
build hash. Python 3.11's platform label says Windows 10 for this build; it ran
on the same Windows 11 host, not a separate Windows 10 validation machine.

NOT TESTED: actual third-party fault reproduction, Windows 10, ARM64, Python
3.13, hosted CI, real mapped SMB drives, pip installation, physical-terminal
Ctrl+C/console closing, power-loss cleanup. TEMP/TMP, profiles/accounts, project
or executable relocation are outside the implemented scope.

Known limits: six samples are not exhaustive; exit 0 needs an app-specific test
oracle; path sensitivity does not prove an encoding cause; inherited dependencies
and environment are not fully snapshotted. Cwd normalization is explicit for
cross-case comparisons. Trusted commands retain user permissions: **not a sandbox**.

The design is suitable for a small one-person maintenance project. Adoption,
customer demand and time savings have not been measured. See RESEARCH.md for
the bounded product judgment and primary-source links.
