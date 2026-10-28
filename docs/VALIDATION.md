# Validation scope

Local native validation: Windows 11 x64 (build 26200), CPython 3.11.15 and 3.12.14,
PowerShell 7.6.5, non-administrator token. Tests use only project-created fixtures.
The local acceptance directory and logs are excluded from Git to avoid exposing
machine-specific paths. A sanitized acceptance summary accompanies this source.

| Area | Status | Evidence / limit |
| --- | --- | --- |
| Six cwd cases, multilingual filenames and repeated runs | PASS | CLI good fixture, 12 executions, exact roundtrip output |
| Simulated non-ASCII-only and general failure | PASS | Different finding categories and exit codes |
| Invalid executable / non-ASCII root | PASS | TOOL_ERROR; not called a Unicode defect |
| Real denied directory creation | PASS | Ephemeral DACL denied WD/AD; restored in finally |
| Timeout / remaining descendant / early parent exit | PASS | Job containment and delayed-write checks |
| Argument spaces/quotes/empty/Unicode/metacharacters | PASS | Child argv matches literal input |
| Malformed bytes / excessive dual-stream output | PASS | Raw bytes retained, decode flagged, cap enforced |
| Ownership, junction and protected sentinel | PASS | Cleanup refuses unsafe tree, target preserved |
| Hard links, replaced run identity, cleanup rename lock | PASS | Refuse foreign objects; real rename attempt denied while cleanup holds handles |
| Mapped network-drive rejection branch | PASS | Drive-type response simulated in a focused test; no real mapping created |
| KeyboardInterrupt cleanup | PASS | Python SIGINT interrupt_main during real sleeping child |
| Real Windows console CTRL_C_EVENT | PASS | R1 isolated console, verified participants, exit 130, target dead, outside sentinel alive |
| Physical keyboard / particular terminal emulator / console closing | NOT TESTED | Controlled OS event is not a human keypress or close-window test |
| Forced kill / power failure filesystem cleanup | NOT TESTED | Can leave run directories; no stale-tree deletion |
| Real affected third-party programs | NOT TESTED | Public-issue research only, no installed repros |
| Windows 10 / ARM64 / Python 3.13+ | NOT TESTED | Outside the verified v0.1.0 release profile |
| Hosted GitHub Actions | NOT TESTED | Workflow provided, no remote created |
| Offline project-local pip target installation | PASS | Existing build tools, no index/deps/download, isolated installed-package execution |
| Actual mapped SMB drive | NOT TESTED | No network-share changes performed |
| Account/profile/TEMP/project/executable relocation | NOT TESTED | Outside implemented scope |

The permission and junction tests alter only their own ephemeral fixture.
No original user projects, permanent environment variables, registry, system PATH
or running applications are modified. Filesystem race resistance against malicious
commands is not claimed. Functional correctness depends on the user's smoke test.

R1 independently reran the original 35 tests before changes and added seven
startup/cleanup regressions. Current review details and evidence references are
in [R1_QUALITY_REVIEW.zh-CN.md](R1_QUALITY_REVIEW.zh-CN.md).

R2 keeps the same core and 42 tests, prepares a Python 3.11/3.12-only Windows
workflow, and verifies the versioned release archive. See
[R2_RELEASE_READINESS.zh-CN.md](R2_RELEASE_READINESS.zh-CN.md) for the final local
release preparation record. No hosted CI or publication is claimed there.
