def check(cmd, mf):
    m = mf.findNode("re")
    if m:
        return {"expected_missing_imports": {"sys.getwindowsversion"}}
