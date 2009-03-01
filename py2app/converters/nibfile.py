"""
Automatic compilation of XIB files
"""
import subprocess, os
from py2app.decorators import converts

@converts(suffix=".xib")
def convert_xib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"

    if dry_run:
        return

    p = subprocess.Popen(['ibtool', '--compile', destination, source])
    xit = p.wait()
    if xit != 0:
        raise RuntimeError("ibtool failed, code %d"%(xit,))


@converts(suffix=".nib")
def convert_nib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"

    if dry_run:
        return

    p = subprocess.Popen(['ibtool', '--compile', destination, source])
    xit = p.wait()
    if xit != 0:
        raise RuntimeError("ibtool failed, code %d"%(xit,))

