#
# Recipe to copy Tcl/Tk support libraries when Python is linked
# with a regular unix install instead of a framework install.
#
import sys
import macholib
import os
import textwrap

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


def check(cmd, mf):
    m = mf.findNode('_tkinter')
    if m is None:
        return None

    prefix = sys.prefix if not hasattr(sys, 'real_prefix') else sys.real_prefix

    paths = []
    lib = os.path.join(prefix, 'lib')
    for fn in os.listdir(lib):
        if not os.path.isdir(os.path.join(lib, fn)):
            continue

        if fn.startswith('tk'):
            tk_path = fn
            paths.append(os.path.join(lib, fn))

        elif fn.startswith('tcl'):
            tcl_path = fn
            paths.append(os.path.join(lib, fn))

    if not paths:
        return None

    prescript = textwrap.dedent("""\
        def _boot_tkinter():
            import os

            resourcepath = os.environ["RESOURCEPATH"]
            os.putenv("TCL_LIBRARY", os.path.join(resourcepath, "lib/%(tcl_path)s"))
            os.putenv("TK_LIBRARY", os.path.join(resourcepath, "lib/%(tk_path)s"))
        _boot_tkinter()
        """) % dict(tcl_path=tcl_path, tk_path=tk_path)

    return dict(resources=[('lib', paths)], prescripts=[StringIO(prescript)])
