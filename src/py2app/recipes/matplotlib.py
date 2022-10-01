import os
import typing

# XXX: Only used for parsing version numbers
import packaging.version
from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("matplotlib")
    if m is None or m.filename is None:
        return None

    # Don't try to import unless we've found the library,
    # otherwise we'll get an error when trying to use
    # py2app on a system with matplotlib
    VER: str
    from matplotlib import __version__ as VER  # type: ignore

    if cmd.matplotlib_backends:
        use_package = False
        for backend in cmd.matplotlib_backends:
            if backend == "-":
                pass

            elif backend == "*":
                mf.import_hook("matplotlib.backends", m, ["*"])

            else:
                mf.import_hook(f"matplotlib.backends.backend_{backend}", m)

    else:
        use_package = True

    # XXX: I don't particularly like this code pattern, repetition is needed
    #      to avoid confusing mypy.
    if use_package:
        if packaging.version.parse(VER) < packaging.version.parse("3.1"):
            return {
                "resources": [os.path.join(os.path.dirname(m.filename), "mpl-data")],
                "prescripts": ["py2app.recipes.matplotlib_prescript"],
                "packages": ["matplotlib"],
            }
        else:
            return {
                "resources": [os.path.join(os.path.dirname(m.filename), "mpl-data")],
                "packages": ["matplotlib"],
            }
    else:
        if packaging.version.parse(VER) < packaging.version.parse("3.1"):
            return {
                "resources": [os.path.join(os.path.dirname(m.filename), "mpl-data")],
                "prescripts": ["py2app.recipes.matplotlib_prescript"],
            }
        else:
            return {
                "resources": [os.path.join(os.path.dirname(m.filename), "mpl-data")],
            }
