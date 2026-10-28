# cwdprobe MVP design

The user explicitly authorized autonomous design and implementation after Go.
No remote repository or release is authorized. Independent nested local repository
on branch `codex/mvp`; surrounding checkout is never edited or staged.

Python 3.11+, standard-library-only runtime. Native Windows 10/11 supported;
non-Windows execution is refused. Core units: workspace ownership/cleanup,
Win32 job lifecycle, bounded binary capture, experiment/classification, CLI.

Input: `python -m cwdprobe --root ASCII_ROOT --report NEW_DIR [options] -- EXE ARGS`.
Resolve executable once before changing cwd; reject batch files and relative
executable paths. Remaining arguments are literal strings, not shell source;
relative data arguments are deliberately relative to each case. No user project
copying. CLI explicitly says only trusted commands; this is not a sandbox.

Require an existing local-drive absolute ASCII root whose ancestor chain has no
reparse points. Root characters restricted to letters, digits, underscore, dot,
hyphen and directory separators to avoid confounding baseline spaces/symbols.
Never silently use a Unicode-profile temp directory as an ASCII baseline.
Create one random owned run directory and fresh case directories per repetition.
Six equal-length leaf names: ASCII, Chinese, Japanese, Korean, spaces, safe ASCII
punctuation. Record actual lengths/code points and do not claim character
causality. No TEMP/TMP overrides, account/profile changes or permanent settings.

Start children suspended, assign a kill-on-close Windows Job Object, resume their
primary thread via documented APIs. Assignment/resume errors fail closed before
user code runs. stdin is closed; stdout/stderr are bounded binary pipes. Deadline
and byte limits terminate the job (including descendants); normal completion also
waits for all job processes to exit and closes it. Ctrl+C cleans the active job and owned workspace. A forced process kill
may leave files but Windows closes the job handle; no automatic stale-directory
deletion. Refuse cleanup of reparse points or unowned/replaced roots. Cleanup holds
ancestor and descendant handles without write/delete sharing and deletes through
verified handles, avoiding check-then-delete path replacement. Conflicts retain
files and produce TOOL_ERROR. Native local drive type and resolved-root syntax
are checked; no mapped network-drive control is accepted.

Two repeats default, finite timeout and capture limit. Record exit status, elapsed
time, state, bytes observed/stored, prefix SHA-256, base64 raw prefix, strict decode
diagnostics and selected OS/codepage/runtime context (no full environment dump).
Complete streams have a full digest; capped streams are explicitly incomplete.

Classify: successful ASCII plus nonzero variant -> PATH_SENSITIVE_FAILURE;
all commands exit nonzero -> GENERAL_FAILURE; failed ASCII with some successes ->
BASELINE_FAILURE (inconclusive); launch/setup/cleanup failure -> TOOL_ERROR;
timeout/output limit/unstable repeats/undecodable or different output ->
INCONCLUSIVE with reasons. Only completed, stable, zero-exit and comparable output
is PASS. Differences never automatically establish Unicode errors. Optional exact
cwd normalization affects comparison only, keeps raw evidence and is disclosed.
Overall precedence: tool/interruption, incomplete/unstable, exit failures, output.
CLI codes: 0 PASS, 1 observed failure, 2 tool error, 3 inconclusive, 130 interrupt.

Report new directory only; JSON and text locally, no upload. Report publication
must exclude local paths/logs via gitignore. Reporting errors produce code 2.
Normal reports are reproducible experiment recipes, not byte-identical timings.

Acceptance: real Windows sample IO in every case; simulated non-ASCII-only and
universal failures; invalid executable; denied write; timeout and surviving
descendants; malformed bytes; oversized output; argv spaces/metacharacters;
repeat consistency; output normalization; Ctrl+C; safe cleanup and reparse refusal;
zipapp build/rebuild hash; stdlib format and metadata checks. ACL test may use only
an ephemeral tool-created directory, restoring it in finally. Other OS/Windows
versions and hosted GitHub CI remain NOT TESTED until actually run.
