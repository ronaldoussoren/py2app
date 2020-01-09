import os


def check(cmd, mf):
    m = mf.findNode("matplotlib")
    if m is None or m.filename is None:
        return None

    if cmd.matplotlib_backends:
        backends = {}
        for backend in cmd.matplotlib_backends:
            if backend == "-":
                pass

            elif backend == "*":
                mf.import_hook("matplotlib.backends", m, ["*"])

            else:
                mf.import_hook("matplotlib.backends.backend_%s" % (backend,), m)

    else:
        backends = {"packages": ["matplotlib"]}

    result = {
        "prescripts": ["py2app.recipes.matplotlib_prescript"],
        "resources": [os.path.join(os.path.dirname(m.filename), "mpl-data")],
    }
    result.update(backends)
    return result
