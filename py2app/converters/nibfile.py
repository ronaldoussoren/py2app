"""
Automatic compilation of XIB files
"""

import os
import subprocess
from subprocess import check_output

from py2app.util import reset_blocking_status

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


def convert_xib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"

    print(f"compile {source} -> {destination}")
    if dry_run:
        return

    with reset_blocking_status():
        subprocess.check_call([_get_ibtool(), "--compile", destination, source])


def convert_nib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"
    print(f"compile {source} -> {destination}")

    if dry_run:
        return

    with reset_blocking_status():
        subprocess.check_call([_get_ibtool, "--compile", destination, source])
