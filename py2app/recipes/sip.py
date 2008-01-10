"""
Py2app support for project using sip, which basicly means PyQt and wrappers
for other Qt-based libraries.

This will include all C modules that might be used when you import a package
using sip because we have no way to fine-tune this.
"""

class Sip(object):
    def __init__(self):
        self.packages = None
        self.warn = None

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

        sipdir = cfg.default_sip_dir
        self.packages = set([
            fn for fn in os.listdir(sipdir)
            if os.path.isdir(os.path.join(sipdir, fn))
        ])

        self.warn = cfg.qt_edition == 'free'
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
            mf.import_hook(pkg, m)
        if self.warn:
            print ''
            print '== PyQt Free Edition GPL warning =='
            print 'Your application is including PyQt Free Edition!'
            print 'Please read the terms of the GPL license before'
            print 'distributing this application!'
            print ''
        return dict()

check = Sip().check
