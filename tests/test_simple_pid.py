import inspect
import os
import time
from multiprocessing import Process
from pathlib import Path
from typing import Union

import psutil as ps
import pytest

from .context import jp


def find_non_existing_pid() -> Union[int, None]:
    """
    Tries to find a non existing pid in the system.
    """
    pids = ps.pids()
    for i in range(1, len(pids)):
        if pids[i - 1] + 1 != pids[i]:
            return pids[i - 1] + 1

    return None


@pytest.fixture(scope="function")  # noqa: PT003
def datadir(tmpdir: str) -> str:
    """
    A fixture for creating a temporary directory.
    """
    frame = inspect.currentframe().f_back
    (_, _, function_name, _, _) = inspect.getframeinfo(frame)
    return tmpdir.mkdir(f"{function_name}")


def test_creating_pid_file(datadir):
    """
    When there is no pid file in a directory,
    the directory should be locked right away.
    """
    path = jp.lock(datadir)
    assert path == Path(datadir / ".pid")
    assert os.path.isfile(path)

    with open(path) as f:
        content = f.read()
        assert content == f"{os.getpid()}"


def test_locking_locked_directory_for_the_same_process(datadir):
    """
    A process should be able to reenter the lock.
    """

    path1 = jp.lock(datadir)
    path2 = jp.lock(datadir)

    assert path1 == path2


def test_locking_locked_directory_different_process(datadir):
    """
    Locking a directory should fail
    if another process has already locked that,
    and the process still exists.
    """

    p = Process(target=lambda: jp.lock(datadir))
    p.start()

    max_tries = 10
    for _ in range(max_tries):
        if Path(datadir / ".pid").is_file():
            break
        else:
            time.sleep(0.1)
    else:
        p.terminate()
        p.join()
        raise AssertionError()

    with pytest.raises(sp.LockException):
        jp.lock(datadir)

    p.terminate()
    p.join()


def test_locking_without_running_a_process(datadir):
    """
    When there is a pid file in a directory,
    with a pid of a non-existing process,
    then it should be possible to lock it.
    """
    pids = sorted(ps.pids())
    for i in range(1, len(pids)):
        if pids[i - 1] + 1 != pids[i]:
            use_pid = pids[i - 1] + 1
            break

    pid_path = Path(datadir / ".pid")

    with open(pid_path, "w+") as f:
        f.write(str(use_pid))

    jp.lock(datadir)
    with open(pid_path, "r") as f:
        pid_content = f.read()

    assert pid_content == str(os.getpid())


def test_unlocking(datadir):
    """
    Unlocking should remove the pid file.
    """

    path = Path(datadir / ".pid")

    assert path.exists() is False
    jp.lock(datadir)
    assert path.exists() is True
    jp.unlock(datadir)
    assert path.exists() is False


def test_unlocking_not_locked_directory(datadir):
    """
    Unlocking a not locked directory should raise an exception.
    """

    with pytest.raises(sp.LockException):
        jp.unlock(datadir)


def test_unlocking_from_another_process_when_locker_runs(datadir):
    """
    Unlocking a directory from another process should not be possible,
    if the locking process runs.
    """

    p = Process(target=lambda: jp.lock(datadir))
    p.start()

    while True:
        if Path(datadir, ".pid").is_file():
            time.sleep(0.1)
            break

    with pytest.raises(sp.LockException):
        jp.unlock(datadir)

    p.terminate()
    p.join()


def test_unlocking_from_another_process_when_locker_doesnt_run(datadir):
    """
    Unlocking a locked directory from another process should work,
    if the locker doesn't run.
    """
    pid = find_non_existing_pid()
    pid_path = Path(datadir / ".pid")
    with open(pid_path, "w") as f:
        f.write(str(pid))

    jp.unlock(datadir)

    assert pid_path.is_file() is False


def test_pidfile_with_garbage_inside(datadir):
    """
    When the pid file contains something else than numbers,
    it should be treated as not locked.
    """
    pid_path = Path(datadir / ".pid")
    with open(pid_path, "w") as f:
        f.write(str("GARBAGE GARBAGE LOTS OF IT"))

    jp.lock(datadir)
    jp.unlock(datadir)


def test_checking_is_locked_functions(datadir):
    """A simple test for checking the `is_locked` function."""
    assert jp.is_locked(datadir) is False
    jp.lock(datadir)
    assert jp.is_locked(datadir) is True
    jp.unlock(datadir)
    assert jp.is_locked(datadir) is False


def test_simple_context_manager(datadir):
    """A simple test for checking the locking context manager."""
    pid_path = jp._make_pid_path(datadir)
    with jp.Lock(datadir) as lock:
        assert lock.directory == datadir
        assert lock.pid_path == pid_path
        assert lock.is_locked
        file_pid = jp._read_pidfile(datadir)
        assert file_pid == os.getpid()

    assert lock.is_locked is False
    assert pid_path.is_file() is False
