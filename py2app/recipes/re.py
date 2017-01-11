def check(cmd, mf):
    m = mf.findNode('re')
    if m:
        return dict(expected_missing_imports=set(['sys.getwindowsversion']))
