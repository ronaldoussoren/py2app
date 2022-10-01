import os
import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("OpenGL")
    if m is None or m.filename is None:
        return None
    p = os.path.splitext(m.filename)[0] + ".py"
    # check to see if it's a patched version that doesn't suck
    if os.path.exists(p):
        for line in open(p):
            if line.startswith("__version__ = "):
                return {}
    # otherwise include the whole damned thing
    return {"packages": ["OpenGL"]}
