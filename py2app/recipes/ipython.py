def check(cmd, mf):
    m = mf.findNode("IPython")
    if m is None or m.filename is None:
        return None

    return {"includes": ['_sitebuiltins']}
