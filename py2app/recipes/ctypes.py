import sys


def check(cmd, mf):
    print("CTYPES USERS", list(mf.getReferers("ctypes")))
    m = mf.findNode("ctypes")
    if m is None or m.filename is None:
        return None

    if sys.version_info[:2] >= (3, 13):
        return {"prescripts": ["py2app.bootstrap.ctypes_setup"], "packages": ["ctypes"]}
    else:
        return {"prescripts": ["py2app.bootstrap.ctypes_setup"]}
