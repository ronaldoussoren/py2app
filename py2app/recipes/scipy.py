def check(cmd, mf):
    m = mf.findNode("scipy")
    if m is None or m.filename is None:
        return None
    return {"packages": ["scipy", "numpy"]}
