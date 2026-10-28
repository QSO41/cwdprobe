"""Documented Win32 job/thread APIs; fail closed before resuming user code."""

import ctypes as c
from ctypes import wintypes as w
import time

k = c.WinDLL("kernel32", use_last_error=True)


class BasicLimits(c.Structure):
    _fields_ = [("ProcessTime", c.c_int64), ("JobTime", c.c_int64),
                ("Flags", w.DWORD), ("MinWorkingSet", c.c_size_t),
                ("MaxWorkingSet", c.c_size_t), ("ActiveProcesses", w.DWORD),
                ("Affinity", c.c_size_t), ("Priority", w.DWORD), ("Scheduling", w.DWORD)]


class IOCounters(c.Structure):
    _fields_ = [(name, c.c_uint64) for name in
                ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes", "OtherBytes")]


class ExtendedLimits(c.Structure):
    _fields_ = [("Basic", BasicLimits), ("IO", IOCounters),
                ("ProcessMemory", c.c_size_t), ("JobMemory", c.c_size_t),
                ("PeakProcessMemory", c.c_size_t), ("PeakJobMemory", c.c_size_t)]


class ThreadEntry(c.Structure):
    _fields_ = [("size", w.DWORD), ("usage", w.DWORD), ("tid", w.DWORD),
                ("pid", w.DWORD), ("base_priority", w.LONG),
                ("delta_priority", w.LONG), ("flags", w.DWORD)]


class Accounting(c.Structure):
    _fields_ = [(name, c.c_int64) for name in ("user", "kernel", "period_user", "period_kernel")] + [
        (name, w.DWORD) for name in ("faults", "total", "active", "terminated")]


def api(name, args, result):
    fn = getattr(k, name)
    fn.argtypes = args
    fn.restype = result
    return fn


create_job = api("CreateJobObjectW", [c.c_void_p, w.LPCWSTR], w.HANDLE)
set_job = api("SetInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL)
assign_job = api("AssignProcessToJobObject", [w.HANDLE, w.HANDLE], w.BOOL)
close_handle = api("CloseHandle", [w.HANDLE], w.BOOL)
open_process = api("OpenProcess", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE)
snapshot = api("CreateToolhelp32Snapshot", [w.DWORD, w.DWORD], w.HANDLE)
first_thread = api("Thread32First", [w.HANDLE, c.POINTER(ThreadEntry)], w.BOOL)
next_thread = api("Thread32Next", [w.HANDLE, c.POINTER(ThreadEntry)], w.BOOL)
open_thread = api("OpenThread", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE)
resume_thread = api("ResumeThread", [w.HANDLE], w.DWORD)
terminate_job = api("TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL)
query_job = api("QueryInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD,
                                             c.POINTER(w.DWORD)], w.BOOL)


def require(value):
    if not value:
        raise c.WinError(c.get_last_error())
    return value


class Job:
    def __init__(self):
        self.handle = require(create_job(None, None))
        limits = ExtendedLimits()
        limits.Basic.Flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        try:
            require(set_job(self.handle, 9, c.byref(limits), c.sizeof(limits)))
        except BaseException:
            self.close()
            raise

    def attach_and_resume(self, pid):
        process = require(open_process(0x0101, False, pid))
        try:
            require(assign_job(self.handle, process))
        finally:
            close_handle(process)
        snap = snapshot(0x4, 0)  # TH32CS_SNAPTHREAD; metadata read only
        if snap == c.c_void_p(-1).value:
            raise c.WinError(c.get_last_error())
        try:
            entry = ThreadEntry()
            entry.size = c.sizeof(entry)
            found = first_thread(snap, c.byref(entry))
            while found:
                if entry.pid == pid:
                    thread = require(open_thread(0x2, False, entry.tid))
                    try:
                        if resume_thread(thread) == 0xFFFFFFFF:
                            raise c.WinError(c.get_last_error())
                        return
                    finally:
                        close_handle(thread)
                entry.size = c.sizeof(entry)
                found = next_thread(snap, c.byref(entry))
            raise OSError("Suspended process primary thread was not found")
        finally:
            close_handle(snap)

    def close(self):
        if self.handle:
            handle, self.handle = self.handle, None
            try:
                require(terminate_job(handle, 1))
                deadline = time.monotonic() + 3
                while True:
                    accounting = Accounting()
                    require(query_job(handle, 1, c.byref(accounting), c.sizeof(accounting), None))
                    if not accounting.active:
                        break
                    if time.monotonic() >= deadline:
                        raise OSError("Job descendants did not finish exiting before cleanup")
                    time.sleep(0.01)
            finally:
                require(close_handle(handle))
