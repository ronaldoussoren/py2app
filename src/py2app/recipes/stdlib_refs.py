"""
Recipe to remove unnecessary imports between stdlib modules
"""

import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo

UNNEEDED_REFS = [
    # module, [ref, ...]
    (
        "pydoc",
        [
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
        ],
    ),
    ("multiprocessing.util", ["test", "test.support"]),
    ("pickle", ["doctest"]),
    ("heapq", ["doctest"]),
    ("pickletools", ["doctest"]),
    ("difflib", ["doctest"]),
]


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    for modname, refs in UNNEEDED_REFS:
        m = mf.findNode(modname)
        if m is None or m.filename is None:
            continue
        for ref in refs:
            mf.removeReference(m, ref)
    return {}
