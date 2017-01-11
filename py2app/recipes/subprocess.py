def check(cmd, mf):
    m = mf.findNode('subprocess')
    if m:
        return dict(expected_missing_imports=set(['_winapi']))
