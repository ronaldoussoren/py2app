def check(cmd, mf):
    m = mf.findNode("mimetypes")
    if m:
        return {"expected_missing_imports": {"winreg"}}
