"""
Automatic compilation of XIB files
"""
import subprocess, os

def convert(source, destination):
    ext = os.path.splitext(source)[-1]
    if ext != '.xib':
        return False

    destination = destination[:-4] + ".nib"

    p = subprocess.Popen(['ibtool', '--compile', destination, source])
    xit = p.wait()
    if xit != 0:
        raise RuntimeError("ibtool failed, code %d"%(xit,))

    return True
