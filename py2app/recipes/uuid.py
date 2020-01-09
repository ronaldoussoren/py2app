def check(cmd, mf):
    m = mf.findNode("uuid")
    if m:
        return {"expected_missing_imports": {"netbios", "win32wnet"}}
