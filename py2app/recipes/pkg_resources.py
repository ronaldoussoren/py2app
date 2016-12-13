def check(cmd, mf):
    m = mf.findNode('pkg_resources')
    if m is None or m.filename is None:
        return None
    for pkg in [
            'packaging', 'pyparsing', 'six', 'appdirs' ]:
        mf.import_hook('pkg_resources._vendor.' + pkg, m, ['*'])
    return dict()
