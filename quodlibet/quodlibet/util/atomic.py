# -*- coding: utf-8 -*-
# Copyright 2013,2015 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

"""Helpers for atomic file operations on Linux/OSX/Windows"""

import os
import contextlib
import tempfile
if os.name == "nt":
    from . import winapi
else:
    import fcntl

from .path import fsnative, is_fsnative


def _windows_rename(source, dest):
    """Replaces dest with source.

    Raises OSError in case of an error.
    """

    assert os.name == "nt"

    # not atomic, but better than removing the original first..
    status = winapi.MoveFileExW(
        source, dest,
        winapi.MOVEFILE_WRITE_THROUGH | winapi.MOVEFILE_REPLACE_EXISTING)

    if status == 0:
        raise winapi.WinError()


@contextlib.contextmanager
def atomic_save(filename, mode):
    """Try to replace the content of a file in the safest way possible.

    A temporary file will be created in the same directory where the
    replacement data can be written into.
    After writing is done the data will be flushed to disk and the original
    file replaced atomically.

    In case of an error this raises IOError and OSError and the original file
    will be untouched. In case the computer crashes or any other
    non-recoverable error happens the temporary file will be left behind and
    has to be deleted manually.

    with atomic_save("config.cfg", "wb") as f:
        f.write(data)
    """

    assert is_fsnative(filename)

    dir_ = os.path.dirname(filename)
    basename = os.path.basename(filename)
    fileobj = tempfile.NamedTemporaryFile(
        mode=mode, dir=dir_,
        prefix=basename + fsnative(u"_"), suffix=fsnative(u".tmp"),
        delete=False)

    try:
        yield fileobj

        fileobj.flush()
        fileno = fileobj.fileno()

        if os.name != "nt" and hasattr(fcntl, "F_FULLFSYNC"):
            # on OSX fsync doesn't sync all the way..
            # https://lists.apple.com/archives/darwin-dev/2005/Feb/msg00072.html
            # https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man2/fsync.2.html
            fcntl.fcntl(fileno, fcntl.F_FULLFSYNC)
        else:
            # on linux fsync goes all the way by default
            # http://linux.die.net/man/2/fsync
            os.fsync(fileno)

        fileobj.close()

        if os.name == "nt":
            _windows_rename(fileobj.name, filename)
        else:
            os.rename(fileobj.name, filename)
    except:
        try:
            os.unlink(fileobj.name)
        except OSError:
            pass
        raise
    finally:
        fileobj.close()
