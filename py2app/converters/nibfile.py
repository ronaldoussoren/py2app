"""
Automatic compilation of XIB files
"""

import subprocess

from py2app.util import _get_tool, reset_blocking_status

gTool = None


def convert_xib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"

    print(f"compile {source} -> {destination}")
    if dry_run:
        return

    with reset_blocking_status():
        subprocess.check_call([_get_tool("ibtool"), "--compile", destination, source])


def convert_nib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"
    print(f"compile {source} -> {destination}")

    if dry_run:
        return

    with reset_blocking_status():
        subprocess.check_call([_get_tool("ibtool"), "--compile", destination, source])
