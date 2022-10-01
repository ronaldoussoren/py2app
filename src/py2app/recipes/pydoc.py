import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("pydoc")
    if m is None or m.filename is None:
        return None
    refs = [
        "Tkinter",
        "tty",
        "BaseHTTPServer",
        "mimetools",
        "select",
        "threading",
        "ic",
        "getopt",
        "tkinter",
        "win32",
    ]
    for ref in refs:
        mf.removeReference(m, ref)
    return {}
