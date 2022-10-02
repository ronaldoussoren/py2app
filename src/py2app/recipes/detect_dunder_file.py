import dis
import os
import sys
import types
import typing

from modulegraph import modulegraph
from modulegraph.modulegraph import ModuleGraph

from py2app.filters import not_stdlib_filter

from .. import build_app
from ._types import RecipeInfo


def get_toplevel_package_name(node: modulegraph.Node) -> typing.Optional[str]:
    if isinstance(node, modulegraph.Package):
        return node.identifier.split(".")[0]
    elif isinstance(node, modulegraph.BaseModule):
        name = node.identifier
        if "." in name:
            return name.split(".")[0]

    return None


def scan_bytecode_loads(names: typing.Set[str], co: types.CodeType) -> None:
    constants = co.co_consts
    for inst in dis.get_instructions(co):
        if inst.opname == "LOAD_NAME":
            assert isinstance(inst.arg, int)
            name = co.co_names[inst.arg]
            names.add(name)

        elif inst.opname == "LOAD_GLOBAL":
            assert isinstance(inst.arg, int)
            if sys.version_info[:2] >= (3, 11):
                name = co.co_names[inst.arg >> 1]
            else:
                name = co.co_names[inst.arg]
            names.add(name)

    cotype = type(co)
    for c in constants:
        if isinstance(c, cotype):
            scan_bytecode_loads(names, c)


# Only activate this recipe for Python 3.4 or later because
# scan_bytecode_loads doesn't work on older versions.


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    packages: typing.Set[str] = set()
    for node in mf.flatten():
        if not not_stdlib_filter(node):
            continue

        if node.code is None:
            continue

        if node.identifier.startswith(os.path.dirname(os.path.dirname(__file__)) + "/"):
            continue

        if not hasattr(node, "_py2app_global_reads"):
            names: typing.Set[str] = set()
            scan_bytecode_loads(names, node.code)
            node._py2app_global_reads = names

        if "__file__" in node._py2app_global_reads:
            pkg = get_toplevel_package_name(node)
            if pkg is not None:
                packages.add(pkg)

    if packages:
        return {"packages": sorted(packages)}
    return None
