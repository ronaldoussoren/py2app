def check(cmd, mf):
    m = mf.findNode('mimetypes')
    if m:
        return dict(expected_missing_imports=set(['winreg']))
