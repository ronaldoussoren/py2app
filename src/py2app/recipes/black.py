import typing

try:
    from importlib.metadata import packages_distributions
except ImportError:
    from importlib_metadata import packages_distributions

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("black")
    if m is None or m.filename is None:
        return None

    # These cannot be in zip
    packages = {"black", "blib2to3"}

    # black may include optimized platform specific C extension which has
    # unusual name, e.g. 610faff656c4cfcbb4a3__mypyc; extract
    # the name from the list of toplevels.
    includes = set()
    for toplevel, dists in packages_distributions.items():  # type: ignore
        if "black" not in dists:
            continue

        includes.add(toplevel)

    includes -= packages

    # Missed dependency
    includes.add("pathspec")

    # XXX: verify if caller knows how to work with sets
    return {"includes": list(includes), "packages": sorted(packages)}
