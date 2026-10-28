# Report contract v1

JSON is the machine-readable source; text is a summary. Status strings and
schema_version are stable for this MVP. Unknown future fields can be ignored.

Top level: tool/version, schema_version, scope, UTC start/end, resolved command
argv, executable SHA-256, settings, selected context, owned workspace,
results, summary, cleanup, limitations, and optional tool error. No environment
dump, hostname, account ID or automatic upload. Paths/argv/output can be private.
Reproduction requires the same command, dependencies, environment and settings;
fresh cwd names, timings and timestamps naturally change.

Each execution: case, repeat, actual cwd, full path ASCII flag and character
length, leaf codepoints, state, exit_code (null if not launched), elapsed_seconds,
stdout, stderr, optional error. States are COMPLETED, LAUNCH_ERROR, TOOL_ERROR,
TIMEOUT, OUTPUT_LIMIT, INTERRUPTED. A forced termination code is not interpreted
as an application's natural failure; state takes precedence.

Each stream: observed_bytes (read before termination), stored_bytes,
truncated, sha256_stored, raw_base64, text (null if strict decoding fails),
decode_error and capture_error. The digest covers exactly stored bytes, never a
claimed full stream when truncated. observed_bytes is not an estimate of everything
the child tried to write. The cap is per stream, per execution. A boundary can
split a multi-byte character; truncated output is already inconclusive.

Interpretation precedence: setup/launch/capture/cleanup error; interruption;
incomplete executions; unstable repeats; all nonzero; failed baseline;
variant nonzero; decoding diagnostics; output difference; PASS. Preserve the
per-execution records even when a higher-priority condition blocks a conclusion.
Expected natural exit code is zero. There is no golden functional-output oracle.

Repeat stability replaces the exact cwd in decoded text to avoid treating fresh
repeat directories as random data. Cross-case text comparison does this only
with explicit normalize_cwd=true. Substitution is case-sensitive, exact native
path spelling only; JSON-escaped, slash-altered or case-changed spellings can
still differ. No regexes, newline folding or timestamp stripping. Raw data never
changes. Stable decoded equality does not imply raw-byte equality across every
possible codec; raw evidence is available for inspection.

Failure to create a report directory / parse CLI arguments returns 2 and prints
an error without pretending a report was written. A report-write failure may leave
a partial new directory; nothing existing is overwritten. Cleanup failure returns
TOOL_ERROR and retains the path in workspace. No automatic recovery deletion.
