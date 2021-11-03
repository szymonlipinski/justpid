import inspect
import os
import time
from multiprocessing import Process

import psutil as ps
import pytest

from .context import sp


def find_non_existing_pid() -> int:
    """
    Tries to find a non existing pid in the system.
    """
    pids = ps.pids()
    for i in range(1, len(pids)):
        if pids[i - 1] + 1 != pids[i]:
            return pids[i - 1] + 1


@pytest.fixture(scope="function")
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
    path = sp.pid_lock(datadir)
    assert path == os.path.join(datadir, ".pid")
    assert os.path.isfile(path)

    with open(path) as f:
        content = f.read()
        assert content == f"{os.getpid()}"


def test_locking_locked_directory_for_the_same_process(datadir):
    """
    A process should be able to reenter the lock.
    """

    path1 = sp.pid_lock(datadir)
    path2 = sp.pid_lock(datadir)

    assert path1 == path2


def test_locking_locked_directory_different_process(datadir):
    """
    Locking a directory should fail
    if another process has already locked that,
    and the process still exists.
    """

    p = Process(target=lambda: sp.pid_lock(datadir))
    p.start()

    while True:
        if os.path.isfile(os.path.join(datadir, ".pid")):
            time.sleep(0.1)
            break

    with pytest.raises(sp.LockException):
        sp.pid_lock(datadir)

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

    pid_path = os.path.join(datadir, ".pid")

    with open(pid_path, "w+") as f:
        f.write(str(use_pid))

    sp.pid_lock(datadir)
    with open(pid_path, "r") as f:
        pid_content = f.read()

    assert pid_content == str(os.getpid())


def test_unlocking(datadir):
    """
    Unlocking should remove the pid file.
    """

    path = os.path.join(datadir, ".pid")

    assert os.path.exists(path) is False
    sp.pid_lock(datadir)
    assert os.path.exists(path) is True
    sp.pid_unlock(datadir)
    assert os.path.exists(path) is False


def test_unlocking_not_locked_directory(datadir):
    """
    Unlocking a not locked directory should raise an exception.
    """

    with pytest.raises(sp.LockException):
        sp.pid_unlock(datadir)


def test_unlocking_from_another_process_when_locker_runs(datadir):
    """
    Unlocking a directory from another process should not be possible,
    if the locking process runs.
    """

    p = Process(target=lambda: sp.pid_lock(datadir))
    p.start()

    while True:
        if os.path.isfile(os.path.join(datadir, ".pid")):
            time.sleep(0.1)
            break

    with pytest.raises(sp.LockException):
        sp.pid_unlock(datadir)

    p.terminate()
    p.join()


def test_unlocking_from_another_process_when_locker_doesnt_run(datadir):
    """
    Unlocking a locked directory from another process should work,
    if the locker doesn't run.
    """
    pid = find_non_existing_pid()
    pid_path = os.path.join(datadir, ".pid")
    with open(pid_path, "w") as f:
        f.write(str(pid))

    sp.pid_unlock(datadir)

    assert os.path.exists(pid_path) is False


def test_pidfile_with_garbage_inside(datadir):
    """
    When the pid file contains something else than numbers,
    it should be treated as not locked.
    """
    pid_path = os.path.join(datadir, ".pid")
    with open(pid_path, "w") as f:
        f.write(str("GARBAGE GARBAGE LOTS OF IT"))

    sp.pid_lock(datadir)
    sp.pid_unlock(datadir)


def test_checking_is_locked_functions(datadir):
    """
    A simple test for checking the `is_locked` function.
    """
    assert sp.is_locked(datadir) is False
    sp.pid_lock(datadir)
    assert sp.is_locked(datadir) is True
    sp.pid_unlock(datadir)
    assert sp.is_locked(datadir) is False


def test_simple_context_manager(datadir):
    """
    A simple test for checking the locking context manager.
    """
    pid_path = sp._make_pid_path(datadir)
    with sp.Lock(datadir) as lock:
        assert lock.directory == datadir
        assert lock.pid_path == pid_path
        assert lock.is_locked
        file_pid = sp._read_pidfile(datadir)
        assert file_pid == os.getpid()

    assert lock.is_locked is False
    assert os.path.exists(pid_path) is False
