import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("sphinx")
    if m is None or m.filename is None:
        return None

    includes = [
        "sphinxcontrib.applehelp",
        "sphinxcontrib.devhelp",
        "sphinxcontrib.htmlhelp",
        "sphinxcontrib.jsmath",
        "sphinxcontrib.qthelp",
        "sphinxcontrib.serializinghtml",
    ]

    return {"includes": includes}
