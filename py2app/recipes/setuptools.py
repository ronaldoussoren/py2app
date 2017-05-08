import sys


def check(cmd, mf):
    m = mf.findNode('pkg_resources')
    if m is None or m.filename is None:
        return None
    for pkg in ['packaging', 'pyparsing', 'six', 'appdirs']:
        mf.import_hook('pkg_resources._vendor.' + pkg, m, ['*'])

    expected_missing_imports = [
        '__main__.__requires__',
        'pkg_resources.extern.pyparsing',
        'pkg_resources.extern.six',
        'pkg_resources._vendor.appdirs']

    if sys.version[0] != 2:
        expected_missing_imports.append('__builtin__')

    return dict(expected_missing_imports=set(expected_missing_imports))
