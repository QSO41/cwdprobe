"""Windows handle-anchored cleanup with locked ancestors and no link traversal."""

import ctypes as c
from ctypes import wintypes as w
import os
from pathlib import Path

k = c.WinDLL("kernel32", use_last_error=True)


def api(name, args, result):
    fn = getattr(k, name)
    fn.argtypes, fn.restype = args, result
    return fn


create_file = api("CreateFileW", [w.LPCWSTR, w.DWORD, w.DWORD, c.c_void_p,
                                  w.DWORD, w.DWORD, w.HANDLE], w.HANDLE)
close_handle = api("CloseHandle", [w.HANDLE], w.BOOL)
set_info = api("SetFileInformationByHandle", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL)
read_file = api("ReadFile", [w.HANDLE, c.c_void_p, w.DWORD, c.POINTER(w.DWORD), c.c_void_p], w.BOOL)
drive_type = api("GetDriveTypeW", [w.LPCWSTR], w.UINT)


class FileInfo(c.Structure):
    _fields_ = [("attributes", w.DWORD), ("created", w.FILETIME),
                ("accessed", w.FILETIME), ("written", w.FILETIME),
                ("volume", w.DWORD), ("size_high", w.DWORD), ("size_low", w.DWORD),
                ("links", w.DWORD), ("index_high", w.DWORD), ("index_low", w.DWORD)]


get_info = api("GetFileInformationByHandle", [w.HANDLE, c.POINTER(FileInfo)], w.BOOL)


def require(value):
    if not value:
        raise c.WinError(c.get_last_error())
    return value


def info(handle):
    result = FileInfo()
    require(get_info(handle, c.byref(result)))
    if result.attributes & 0x400:
        raise ValueError("Cleanup refuses reparse points")
    return result


def lock_path(path, delete=False, read=False):
    # OPEN_REPARSE_POINT inspects the final component itself. Previously locked
    # ancestors cannot be replaced because FILE_SHARE_DELETE is deliberately off.
    access = 0x80 | (0x10000 if delete else 0) | (0x80000000 if read else 0)
    # Deny write opens as well, so a directory cannot become a reparse point
    # while its children are being inventoried. Existing conflicting handles
    # make cleanup fail closed before deletion.
    handle = create_file(str(path), access, 0x1, None, 3, 0x02200000, None)
    if handle == c.c_void_p(-1).value:
        raise c.WinError(c.get_last_error())
    return handle


class Disposition(c.Structure):
    _fields_ = [("delete", c.c_ubyte)]  # native BOOLEAN, not Win32 BOOL


def delete_handle(handle):
    disposition = Disposition(1)  # FileDispositionInfo (4)
    require(set_info(handle, 4, c.byref(disposition), c.sizeof(disposition)))


def safe_cleanup(workspace):
    handles = []
    entries = []
    marker_handle = None
    marker = workspace.path / ".cwdprobe-owner"
    try:
        # Lock from the drive root down before opening any run descendants.
        for ancestor in reversed(workspace.path.parents):
            handle = lock_path(ancestor)
            handles.append(handle)
            if not info(handle).attributes & 0x10:
                raise ValueError("Cleanup ancestor is not a directory")

        def inventory(path, depth=0):
            nonlocal marker_handle
            if depth > 40 or len(handles) > 20000:
                raise ValueError("Cleanup inventory exceeds safety limit; directory retained")
            if not path.is_relative_to(workspace.path):
                raise ValueError("Cleanup target outside owned run")
            handle = lock_path(path, delete=True, read=(path == marker))
            handles.append(handle)
            metadata = info(handle)
            directory = bool(metadata.attributes & 0x10)
            if path == workspace.path:
                # Root is locked now; the pathname cannot be swapped during stat.
                current = path.stat()
                if (current.st_dev, current.st_ino) != workspace.identity:
                    raise ValueError("Owned run directory was replaced")
            if directory:
                with os.scandir(path) as scan:
                    for entry in scan:
                        inventory(Path(entry.path), depth + 1)
            elif metadata.links != 1 or metadata.attributes & 0x40:
                raise ValueError("Cleanup refuses hard links and special files")
            if path == marker:
                if directory:
                    raise ValueError("Ownership marker is not a file")
                marker_handle = handle
            else:
                entries.append((path, handle))

        inventory(workspace.path)
        if marker_handle is None:
            raise ValueError("Ownership marker is missing")
        data = c.create_string_buffer(64)
        count = w.DWORD()
        require(read_file(marker_handle, data, 64, c.byref(count), None))
        if data.raw[:count.value] != workspace.token.encode("ascii"):
            raise ValueError("Ownership marker does not match")
        # Preflight is complete. Delete by the verified handles, not re-resolved
        # pathnames. Keep the marker until all other descendants have been removed.
        ordered = entries[:-1] + [(marker, marker_handle), entries[-1]]
        for path, handle in ordered:
            info(handle)
            delete_handle(handle)
            require(close_handle(handle))
            handles.remove(handle)
    finally:
        for handle in reversed(handles):
            close_handle(handle)
