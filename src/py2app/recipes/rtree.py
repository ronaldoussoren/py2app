import os
import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("rtree")
    if m is None or m.filename is None:
        return None
    if m.packagepath is None:
        return None

    try:
        rtree_dylibs = os.scandir(os.path.join(m.packagepath[0], "lib"))
    except OSError:
        return None

    frameworks = [lib.path for lib in rtree_dylibs]

    return {"frameworks": frameworks}
