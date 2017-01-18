def check(cmd, mf):
    m = mf.findNode('importlib')
    if m:
        return dict(expected_missing_imports=set(
                    ['_frozen_importlib_external']))

    return None
