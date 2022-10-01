import os
import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("zmq")
    if m is None or m.filename is None:
        return None
    if m.packagepath is None:
        return None

    dylibs = os.scandir(os.path.join(m.packagepath[0], ".dylibs"))
    frameworks = [lib.path for lib in dylibs]

    return {"frameworks": frameworks}
