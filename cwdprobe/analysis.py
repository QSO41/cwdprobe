"""Conservative interpretation; observed path sensitivity is not causality."""


def classify(rows, normalize_cwd=False):
    def result(status, finding):
        return {"status": status, "finding": finding}

    if not rows or not any(r["case"] == "ascii" for r in rows):
        return result("TOOL_ERROR", "MISSING_BASELINE")
    states = {r["state"] for r in rows}
    if states & {"LAUNCH_ERROR", "TOOL_ERROR"}:
        return result("TOOL_ERROR", "EXECUTION_ERROR")
    if "INTERRUPTED" in states:
        return result("INTERRUPTED", "INTERRUPTED")
    if states != {"COMPLETED"}:
        return result("INCONCLUSIVE", "INCOMPLETE_EXECUTION")

    def signature(r, normalize=None):
        values = [r["exit_code"]]
        for name in ("stdout", "stderr"):
            stream = r[name]
            value = stream["text"]
            if (normalize_cwd if normalize is None else normalize) and value is not None:
                value = value.replace(r["cwd"], "<CWD>")
            values.extend((value, stream["decode_error"]))
        return tuple(values)

    grouped = {}
    for r in rows:
        # Fresh repeat directories intentionally differ. Ignore only their exact
        # cwd in the repeat-stability check; cross-case normalization is opt-in.
        grouped.setdefault(r["case"], set()).add(signature(r, True))
    if any(len(values) != 1 for values in grouped.values()):
        return result("INCONCLUSIVE", "UNSTABLE_REPEATS")
    if all(r["exit_code"] != 0 for r in rows):
        return result("FAIL", "GENERAL_FAILURE")
    baseline = [r for r in rows if r["case"] == "ascii"]
    if any(r["exit_code"] != 0 for r in baseline):
        return result("INCONCLUSIVE", "BASELINE_FAILURE")
    if any(r["exit_code"] != 0 for r in rows):
        return result("FAIL", "PATH_SENSITIVE_FAILURE")
    if any(r[s]["decode_error"] for r in rows for s in ("stdout", "stderr")):
        return result("INCONCLUSIVE", "DECODE_ERROR")
    if len({signature(r) for r in rows}) != 1:
        return result("INCONCLUSIVE", "OUTPUT_DIFFERENCE")
    return result("PASS", "NO_DIFFERENCE_OBSERVED")
