"""Bounded binary capture and a whole-process-tree execution deadline."""

import base64
from contextlib import contextmanager
import hashlib
import signal
import subprocess
import threading
import time

from .winjob import Job


@contextmanager
def _defer_sigint():
    """Deliver Ctrl+C after a short resource-ownership transition is complete."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.getsignal(signal.SIGINT)
    if previous == signal.SIG_IGN:
        yield
        return
    pending = None

    def defer(signum, frame):
        nonlocal pending
        pending = (signum, frame)

    signal.signal(signal.SIGINT, defer)
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        signal.signal(signal.SIGINT, previous)
        if pending is not None and not failed:
            if callable(previous):
                previous(*pending)
            else:
                raise KeyboardInterrupt


class Capture:
    def __init__(self, pipe, limit, exceeded):
        self.pipe, self.limit, self.exceeded = pipe, limit, exceeded
        self.data = bytearray()
        self.seen = 0
        self.error = None
        self.thread = threading.Thread(target=self.read, daemon=True)

    def read(self):
        try:
            while chunk := self.pipe.read(65536):
                self.seen += len(chunk)
                self.data.extend(chunk[:max(0, self.limit - len(self.data))])
                if self.seen > self.limit:
                    self.exceeded.set()
        except OSError as exc:
            self.error = str(exc)

    def report(self, encoding):
        raw = bytes(self.data)
        try:
            text, error = raw.decode(encoding, errors="strict"), None
        except UnicodeError as exc:
            text, error = None, str(exc)
        return {"observed_bytes": self.seen, "stored_bytes": len(raw),
                "truncated": self.seen > len(raw), "sha256_stored": hashlib.sha256(raw).hexdigest(),
                "raw_base64": base64.b64encode(raw).decode("ascii"),
                "text": text, "decode_error": error, "capture_error": self.error}


def run_process(command, cwd, timeout, max_bytes, encoding):
    start = time.monotonic()
    state, error, proc, job = "COMPLETED", None, None, None
    captures = []
    exceeded = threading.Event()
    try:
        job = Job()
        # Popen can be interrupted after CreateProcess but before returning.
        # Own its object and both reader threads before delivering SIGINT;
        # user code is still suspended and is not resumed on cancellation.
        with _defer_sigint():
            try:
                proc = subprocess.Popen(
                    command, cwd=cwd, shell=False, stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
                    creationflags=0x00000004 | subprocess.CREATE_NO_WINDOW)  # CREATE_SUSPENDED
            except OSError as exc:
                state, error = "LAUNCH_ERROR", str(exc)
            if proc:
                captures = [Capture(proc.stdout, max_bytes, exceeded),
                            Capture(proc.stderr, max_bytes, exceeded)]
                for capture in captures:
                    capture.thread.start()
        if proc:
            job.attach_and_resume(proc.pid)
            deadline = start + timeout
            while proc.poll() is None:
                if exceeded.wait(0.01):
                    state = "OUTPUT_LIMIT"
                    break
                if time.monotonic() >= deadline:
                    state = "TIMEOUT"
                    break
    except KeyboardInterrupt:
        state = "INTERRUPTED"
    except (OSError, RuntimeError) as exc:
        state, error = "TOOL_ERROR", str(exc)
    finally:
        # Even normal parent exit must close descendants that hold pipe handles.
        try:
            with _defer_sigint():
                if job:
                    try:
                        job.close()
                    except OSError as exc:
                        state, error = "TOOL_ERROR", str(exc)
                if proc:
                    if proc.poll() is None:
                        proc.kill()  # also covers failure before job assignment
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        state, error = "TOOL_ERROR", "Child did not terminate after job close"
                    for capture in captures:
                        if capture.thread.ident is not None:
                            capture.thread.join(timeout=3)
                        if capture.thread.is_alive():
                            state, error = "TOOL_ERROR", "Capture pipe did not close"
                        else:
                            capture.pipe.close()
                    if not captures:
                        for pipe in (proc.stdout, proc.stderr):
                            if pipe:
                                pipe.close()
                    if state == "COMPLETED" and exceeded.is_set():
                        state = "OUTPUT_LIMIT"
                    if any(cap.error for cap in captures):
                        state, error = "TOOL_ERROR", "Binary capture failed"
        except KeyboardInterrupt:
            if state != "TOOL_ERROR":
                state = "INTERRUPTED"
    empty = {"observed_bytes": 0, "stored_bytes": 0, "truncated": False,
             "sha256_stored": hashlib.sha256(b"").hexdigest(), "raw_base64": "",
             "text": "", "decode_error": None, "capture_error": None}
    streams = [cap.report(encoding) for cap in captures]
    return {"state": state, "error": error,
            "exit_code": proc.returncode if proc else None,
            "elapsed_seconds": round(time.monotonic() - start, 6),
            "stdout": streams[0] if streams else empty.copy(),
            "stderr": streams[1] if streams else empty.copy()}
