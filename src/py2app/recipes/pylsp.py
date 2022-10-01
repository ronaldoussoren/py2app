import os
import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("pylsp")
    if m is None or m.filename is None:
        return None
    if m.packagepath is None:
        return None

    includes = ["pylsp.__main__", "pylsp.python_lsp"]

    root_dir = m.packagepath[0]
    files = os.scandir(os.path.join(root_dir, "plugins"))
    for file in files:
        if file.name.endswith(".py"):
            includes.append(".".join(["pylsp", "plugins", file.name[:-3]]))

    return {"includes": includes}
