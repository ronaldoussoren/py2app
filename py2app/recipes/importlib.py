def check(cmd, mf):
    m = mf.findNode("importlib")
    if m:
        return {"expected_missing_imports": {"_frozen_importlib_external"}}

    return None
