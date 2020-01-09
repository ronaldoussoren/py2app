def check(cmd, mf):
    m = mf.findNode("os")
    if m:
        return {"expected_missing_imports": {"nt"}}
