"""
Automatic compilation of XIB files
"""
from __future__ import print_function
import subprocess, os
from py2app.decorators import converts

gTool = None
def _get_ibtool():
    global gTool
    if gTool is None:
        if os.path.exists('/usr/bin/xcrun'):
            gTool = subprocess.check_output(['/usr/bin/xcrun', '-find', 'ibtool'])[:-1]
        else:
            gTool = 'ibtool'

    print (gTool)
    return gTool

@converts(suffix=".xib")
def convert_xib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"

    print("compile %s -> %s"%(source, destination))
    if dry_run:
        return

    subprocess.check_call([_get_ibtool(), '--compile', destination, source])

@converts(suffix=".nib")
def convert_nib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"
    print("compile %s -> %s"%(source, destination))

    if dry_run:
        return

    subprocess.check_call([_get_ibtool, '--compile', destination, source])
