import os
import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("pygame")
    if m is None or m.filename is None:
        return None

    def addpath(f: str) -> str:
        assert m is not None
        assert m.filename is not None
        return os.path.join(os.path.dirname(m.filename), f)

    RESOURCES = ["freesansbold.ttf", "pygame_icon.icns"]
    return {"loader_files": [("pygame", list(map(addpath, RESOURCES)))]}
