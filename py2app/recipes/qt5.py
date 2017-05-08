import sys
from modulegraph.modulegraph import MissingModule


def check(cmd, mf):
    m = mf.findNode('PyQt5')
    if m and not isinstance(m, MissingModule):
        try:
            # PyQt5 with sipconfig module, handled
            # by sip recipe
            import sipconfig  # noqa: F401
            return None

        except ImportError:
            pass

        # All imports are done from C code, hence not visible
        # for modulegraph
        # 1. Use of 'sip'
        # 2. Use of other modules, datafiles and C libraries
        #    in the PyQt5 package.
        mf.import_hook('sip', m)
        if sys.version[0] != 2:
            return dict(
                packages=['PyQt5'],
                expected_missing_imports={'copy_reg', 'cStringIO', 'StringIO'})
        else:
            return dict(packages=['PyQt5'])

    return None
