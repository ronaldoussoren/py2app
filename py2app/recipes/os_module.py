def check(cmd, mf):
    m = mf.findNode('os')
    if m:
        return dict(expected_missing_imports=set(['nt']))
