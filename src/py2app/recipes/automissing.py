import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo

AUTO_MISSING = [
    ("importlib", ("_frozen_importlib_external",)),
    ("mimetypes", ("winreg",)),
    ("os", ("nt",)),
    ("re", ("sys.getwindowsversion",)),
    ("subprocess", ("_winapi",)),
    (
        "uuid",
        (
            "netbios",
            "win32wnet",
        ),
    ),
]


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    to_return: typing.List[str] = []
    for python_package, expected_missing in AUTO_MISSING:
        m = mf.findNode(python_package)
        if m is None or m.filename is None:
            continue

        to_return.extend(expected_missing)

    if to_return:
        return {"expected_missing_imports": set(to_return)}
    return None
