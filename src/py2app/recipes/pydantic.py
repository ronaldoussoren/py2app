import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo

PYDANTIC_IMPORTS = [
    "abc",
    "collections",
    "collections.abc",
    "colorsys",
    "configparser",
    "contextlib",
    "copy",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "fractions",
    "functools",
    "ipaddress",
    "itertools",
    "json",
    "math",
    "os",
    "pathlib",
    "pickle",
    "re",
    "sys",
    "types",
    "typing",
    "typing_extensions",
    "uuid",
    "warnings",
    "weakref",
]


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("pydantic")
    if m is None or m.filename is None:
        return None

    # Pydantic Cython and therefore hides imports from the
    # modulegraph machinery
    return {"packages": ["pydantic"], "includes": PYDANTIC_IMPORTS}
