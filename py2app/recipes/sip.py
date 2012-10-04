"""
Py2app support for project using sip, which basicly means PyQt and wrappers
for other Qt-based libraries.

This will include all C modules that might be used when you import a package
using sip because we have no way to fine-tune this.

The problem with SIP is that all inter-module depedencies (for example from
PyQt4.Qt to PyQt4.QtCore) are handled in C code and therefore cannot be 
detected by the python code in py2app).
"""

import sys

class Sip(object):
    def __init__(self):
        self.packages = None

    def config(self):
        if self.packages is not None:
            return self.packages

        import sipconfig, os
        try:
            set
        except NameError:
            from sets import Set as set

        ##old version for PyQt/Qt 3
        # cfg = sipconfig.Configuration()
        # qtdir = cfg.qt_lib_dir

        ##new version for PyQt 4
        from PyQt4 import pyqtconfig
        cfg = pyqtconfig.Configuration()
        qtdir = cfg.qt_lib_dir
        if not os.path.exists(qtdir):
            # half-broken installation? ignore.
            raise ImportError

        # Qt is GHETTO!
        dyld_library_path = os.environ.get('DYLD_LIBRARY_PATH', '').split(':')

        if qtdir not in dyld_library_path:
            dyld_library_path.insert(0, qtdir)
            os.environ['DYLD_LIBRARY_PATH'] = ':'.join(dyld_library_path)

        sipdir = os.path.dirname(cfg.pyqt_mod_dir)
        self.packages = set()

        for fn in os.listdir(sipdir):
            fullpath = os.path.join(sipdir, fn)
            if os.path.isdir(fullpath):
                self.packages.add(fn)
                if fn == 'PyQt4':
                    # PyQt4 has a nested structure, also import
                    # subpackage to ensure everything get seen.
                    for sub in os.listdir(fullpath):
                        if ".py" not in sub:
                            self.packages.add('%s.%s'%(fn, sub.replace(".so","")))                            

        # Causes a python3-related syntax error (metaclass keyword),
        # and you probably don't need it:
        if "PyQt4.uic" in self.packages and sys.version_info.major != 3:
            print("WARNING: PyQt uic module found.")
            print("avoid python3 metaclass syntax errors by adding 'PyQt4.uic' to your excludes option.")

        return self.packages

    def check(self, cmd, mf):
        try:
            packages = self.config()
        except ImportError:
            return dict()

        for pkg in packages:
            m = mf.findNode(pkg)
            if m is not None and m.filename is not None:
                break
        else:
            return None

        mf.import_hook('sip', m)
        m = mf.findNode('sip')
        # naive inclusion of ALL sip packages
        # stupid C modules.. hate hate hate
        for pkg in packages:
            try:
                mf.import_hook(pkg, m)
            except ImportError as exc:
                print("WARNING: ImportError in sip recipe ignored: %s"%(exc,))

        return dict()

check = Sip().check
