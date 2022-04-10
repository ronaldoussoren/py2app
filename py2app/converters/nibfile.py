"""
Automatic compilation of XIB files
"""

import os
import subprocess

from py2app.decorators import converts
from py2app.util import check_output


# _run_nibtool is an experiment while researching an odd
# failure of py2app: when _run_nibtool is None py2app will often
# (but for from every time) fail when there are NIB files in the
# project.  The failure is very odd: writing to sys.stderr fails
# with EGAIN as the errno, and subsequently the interpreter basically
# crashes.
#
# This workaround seems to fix that issue for now.
#
def _run_nibtool(source, destination):
    pid = os.fork()
    if pid == 0:
        os.setsid()
        xit = subprocess.call([_get_ibtool(), "--compile", destination, source])
        os._exit(xit)
    else:
        pid, status = os.waitpid(pid, 0)
        if os.WEXITSTATUS(status) != 0:
            raise RuntimeError(f"ibtool failed ({source!r} -> {destination!r})")


gTool = None


def _get_ibtool():
    global gTool
    if gTool is None:
        if os.path.exists("/usr/bin/xcrun"):
            try:
                gTool = check_output(["/usr/bin/xcrun", "-find", "ibtool"])[:-1]
            except subprocess.CalledProcessError:
                raise OSError("Tool 'ibtool' not found")
        else:
            gTool = "ibtool"

    return gTool


@converts(suffix=".xib")
def convert_xib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"

    print(f"compile {source} -> {destination}")
    if dry_run:
        return

    if _run_nibtool is None:
        subprocess.check_call([_get_ibtool(), "--compile", destination, source])
    else:
        _run_nibtool(source, destination)


@converts(suffix=".nib")
def convert_nib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"
    print(f"compile {source} -> {destination}")

    if dry_run:
        return

    if _run_nibtool is None:
        subprocess.check_call([_get_ibtool, "--compile", destination, source])
    else:
        _run_nibtool(source, destination)
