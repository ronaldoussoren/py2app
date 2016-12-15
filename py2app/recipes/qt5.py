def check(cmd, mf):
    if mf.findNode('PyQt5'):
        try:
            # PyQt5 with sipconfig module, handled
            # by sip recipe
            import sipconfig
            return None

        except ImportError:
            pass

        return dict(packages=['PyQt5'])
    return None
