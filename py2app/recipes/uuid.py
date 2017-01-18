def check(cmd, mf):
    m = mf.findNode('uuid')
    if m:
        return dict(expected_missing_imports=set(['netbios', 'win32wnet']))
