def check(cmd, mf):
    m = mf.findNode("tensorflow")
    if m is None or m.filename is None:
        return None

    return {"packages": ["tensorflow"]}
