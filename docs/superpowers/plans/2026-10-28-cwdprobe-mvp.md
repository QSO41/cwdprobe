# cwdprobe implementation plan

Goal: deliver the bounded design as a locally verifiable Windows CLI.
Architecture: standard-library Python with one Win32 lifecycle adapter.
Tech stack: Python 3.11+, ctypes, subprocess, unittest, JSON, zipfile.
Execution: inline, as authorized by the user; independent review at completion.

Global constraints: no third-party runtime packages; cwd-only; local reports;
trusted commands only; existing local ASCII root; no user-project scanning;
no global installation or system changes; no GitHub publication.

- [x] Workspace and result protocol: `workspace.py`, `analysis.py`, tests.
  Write failing behavior tests first: mixed failures -> path-sensitive; all
  nonzero -> general; no ASCII -> reject; foreign marker -> refuse cleanup.
  Run `python -m unittest discover -s tests -v`, then implement and rerun.
- [x] Process runner: `winjob.py`, `process.py`, `tests/test_process.py`.
  Real child tests first for argv, timeout, descendants, undecodable bytes and
  byte cap. Start suspended, attach job, resume documented thread; on any setup
  error terminate before execution. Verify thread captures stay bounded.
- [x] Experiment and CLI: `experiment.py`, `__main__.py`, examples and tests.
  CLI subprocess tests first for PASS, simulated path failure, all-fail,
  invalid command, output difference and repeat behavior. No fixture copying.
  `run_experiment(command, root, repeats, timeout, max_bytes, encoding,
  normalize_cwd)` returns a JSON-serializable dict; `main()` writes new local
  report directory, prints concise status and returns documented exit code.
- [x] Lifecycle acceptance: denied writes, junction refusal, interruption and
  normal parent with lingering child. Tests operate on their own fixtures only.
- [x] Documentation and packaging: English/Chinese READMEs, MIT, metadata,
  deterministic stdlib zipapp, CI, quality checks and acceptance record.
  Verify via `python tools/check.py`, `python -m unittest discover -s tests -v`,
  `python tools/build.py` twice and compare SHA-256. Review source/diff for
  sensitive paths and verify surrounding checkout unchanged except new folder.

Red/green cycles were observed during implementation. No placeholder
features, external faulty applications or public release needed for acceptance.

Final verification: 35 native Windows tests pass on both Python 3.11 and 3.12. Review fixes add `winfs.py`
handle-anchored cleanup, deny-write/delete locks, network drive validation,
UnicodeError byte preservation and a job active-process shutdown wait.
Initial red runs were observed in the development session, not copied into the
final acceptance bundle; the bundle contains the final green suite only.
