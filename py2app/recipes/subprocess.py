def check(cmd, mf):
    m = mf.findNode("subprocess")
    if m:
        return {"expected_missing_imports": {"_winapi"}}
