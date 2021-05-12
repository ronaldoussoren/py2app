import os
from matplotlib import __version__ as VER
from pkg_resources import packaging


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
        "resources": [os.path.join(os.path.dirname(m.filename), "mpl-data")],
    }
    if packaging.version.parse(VER) < packaging.version.parse('3.1'):
        result.update({"prescripts": ["py2app.recipes.matplotlib_prescript"]})

    result.update(backends)
    return result
