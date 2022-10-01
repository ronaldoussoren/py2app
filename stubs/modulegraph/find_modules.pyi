""" """
import typing
from .modulegraph import Node, ModuleGraph

PY_SUFFIXES: list[str]
C_SUFFIXES: list[str]

find_modules, find_needed_modules, parse_mf_results

def get_implies() -> dict[str, list[str]]: ...
def parse_mf_results(mf: ModuleGraph) -> tuple[list[Node], list[Node]]: ...
def find_needed_modules(
    mf: ModuleGraph | None = None,
    scripts: typing.Sequence[str] = (),
    includes: typing.Sequence[str] = (),
    packages: typing.Sequence[str] = (),
) -> ModuleGraph: ...
def find_modules(
    scripts: typing.Sequence[str] = (),
    includes: typing.Sequence[str] = (),
    packages: typing.Sequence[str] = (),
    excludes: typing.Sequence[str] = (),
    path: typing.Sequence[str] | None = None,
    debug: int = 0,
) -> ModuleGraph: ...
