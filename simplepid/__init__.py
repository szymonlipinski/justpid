import contextlib
import os
import re
from pathlib import Path
from typing import Union

import psutil as ps

pid_file_name = ".pid"


class LockException(Exception):
    pass


def _make_pid_path(directory: str) -> Path:
    return Path(directory / pid_file_name)


def _read_pidfile(directory: str) -> Union[None, int]:
    """Reads a pid file, checks if the content is valid.
    Returns the pid value from the file or None if there is not valid value.

    :param directory: directory to read the pid file from
    :returns: value from the pid file or None if the file doesn't exist
              or the value is not a valid integer
    """
    pid_path = _make_pid_path(directory)
    with contextlib.suppress(FileNotFoundError), open(pid_path, "r") as f:
        data = f.read()
        if re.match("^[0-9]+$", data):
            return int(data)
    return None


def _write_pidfile(directory: str, pid: int = None) -> None:
    """Writes the pid to the pidfile in the directory.

    :param directory: directory for the pid file
    :pid: pid to write, defaults to the current process id

    """
    pid = pid or os.getpid()
    with open(_make_pid_path(directory), "w+") as f:
        f.write(str(pid))


def _does_pid_exist(pid: int) -> bool:  # noqa: FNE005
    if pid is None:
        return False
    return ps.pid_exists(pid)


def is_locked(directory: str) -> bool:
    pid = _read_pidfile(directory)
    if pid is None:
        return False
    return _does_pid_exist(pid)


def is_locked_by_self(directory: str) -> bool:
    return _read_pidfile(directory) == os.getpid()


def pid_lock(directory: str):
    """Locks a directory creating a pid file..."""
    path = _make_pid_path(directory)

    file_pid = _read_pidfile(directory)
    self_pid = os.getpid()

    # The pid file has this process id, so we allow to lock it again.
    if file_pid == self_pid:
        return path

    # If the pid stored in the pid file exists in the system,
    # we should not allow to lock it.
    if file_pid is not None and ps.pid_exists(file_pid):
        p = ps.Process(file_pid)
        raise LockException(
            f"The directory {directory} is already locked by "
            f"pid: {p.pid} - {p.cmdline()}"
        )

    _write_pidfile(directory, self_pid)

    return path


def pid_unlock(directory: str) -> None:
    """Removes the pid file only if it's locked by the current process
    or the process with the file's pid doesn't exist.
    """

    path = _make_pid_path(directory)

    file_pid = _read_pidfile(directory)

    if _does_pid_exist(file_pid) and file_pid != os.getpid():
        raise LockException(
            f"Cannot unlock the directory {directory} because "
            f"it's locked by a running process with pid = {file_pid}."
        )

    try:
        os.remove(path)
    except FileNotFoundError:
        raise LockException(f"Cannot unlock a not locked directory {directory}.")


class Lock:
    def __init__(self, directory: str):
        self._directory = directory

    @property
    def directory(self):
        return self._directory

    @property
    def pid_path(self):
        return _make_pid_path(self._directory)

    @property
    def is_locked(self) -> bool:
        return is_locked_by_self(self._directory)

    def __enter__(self):
        pid_lock(self._directory)
        return self

    def __exit__(self, type, value, traceback):  # noqa: A002
        pid_unlock(self._directory)
