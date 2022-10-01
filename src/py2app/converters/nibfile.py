"""
Automatic compilation of XIB files
"""

import os
import subprocess
import typing

from py2app.util import get_tool, reset_blocking_status

gTool = None


def convert_xib(
    source: typing.Union[os.PathLike[str], str],
    destination: typing.Union[os.PathLike[str], str],
    dry_run: bool = False,
) -> None:
    destination = os.fspath(destination)[:-4] + ".nib"

    print(f"compile {source} -> {destination}")
    if dry_run:
        return

    with reset_blocking_status():
        subprocess.check_call([get_tool("ibtool"), "--compile", destination, source])


def convert_nib(
    source: typing.Union[os.PathLike[str], str],
    destination: typing.Union[os.PathLike[str], str],
    dry_run: bool = False,
) -> None:
    destination = os.fspath(destination)[:-4] + ".nib"
    print(f"compile {source} -> {destination}")

    if dry_run:
        return

    with reset_blocking_status():
        subprocess.check_call([get_tool("ibtool"), "--compile", destination, source])
