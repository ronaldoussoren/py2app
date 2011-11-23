def check(cmd, mf):
    name = 'PySide'
    m = mf.findNode(name)
    if m is None or m.filename is None:
        return None

    # PySide dumps some of its shared files
    # into /usr/lib, which is a system location
    # and those files are therefore not included
    # into the app bundle by default.
    from macholib.util import NOT_SYSTEM_FILES
    NOT_SYSTEM_FILES

    import os, sys
    for fn in os.listdir('/usr/lib'):
        add=False
        if fn.startswith('libpyside-python'):
            add=True
        elif fn.startswith('libshiboken-python'):
            add=True
        if add:
            NOT_SYSTEM_FILES.append(os.path.join('/usr/lib', fn)) 

    return dict()
