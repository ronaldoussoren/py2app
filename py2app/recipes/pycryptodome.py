def check(cmd, mf):
    m = mf.findNode("Crypto")
    if m is None or m.filename is None:
        return None

    # pycryptodome contains C libraries
    # that are loaded using ctypes and are
    # not detected by the regular machinery.
    # Just bail out and include this package
    # completely and in the filesystem.
    return {"packages": ["Crypto"]}
