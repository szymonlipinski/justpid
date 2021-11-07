
Introduction
====================

The JustPidFile libraray is a very simple, yet functional, pid file implementation.

This way the first process accessing the pid file, is able to write there its
PID (Process ID). The next one will check the file, the pid inside, and will
check if the process with the PID exists. If it exists, then an exception is thrown.

If the pid file doesn't exist, or contains garbage data, or an integer with a PID
of a not running process, then the directory can be "locked".

"Locking" a directory is done by creating a ".pid" file in the directory
with the locking process ID inside.

Gotchas
--------------------

Locking a directory with a simple file works as long as everybody uses the same
mechanism.
There is nothing that forbids any other process to change files in the "locked"
directory. The purpose of this library is to avoid having two processes writing
to the same files at the same time.

Example
--------------------

Lock a directory using the simple functional API

.. code-block:: python

    import justpid as jp
    directory = "abc"

    try:
        jp.lock(directory)
        # some logic
        jp.unlock(directory)
    except jp.LockException:
        print("Cannot lock a directory")



Use a context manager to automatically unlock the directory at the end

.. code-block:: python

    import justpid as jp

    with jp.Lock(directory):
        # do something here
        # the directory is exlusively locked
    # and here is unlocked

Implementation Details
-----------------------

There are some hardcoded things like:

* The pid file is in side the locked directory and is named `.pid`
* The main api is made of functions.
* There is also a context manager, just to make life a little bit simpler.



Do You Need this?
----------------------

Maybe? Who knows. I need.


