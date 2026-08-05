""" """

import typing

from .modulegraph import Extension, ModuleGraph, Node

PY_SUFFIXES: list[str]
C_SUFFIXES: list[str]

find_modules, find_needed_modules, parse_mf_results

def get_implies() -> dict[str, list[str]]: ...
def parse_mf_results(mf: ModuleGraph) -> tuple[list[Node], list[Extension]]: ...
def find_needed_modules(
    mf: ModuleGraph | None = None,
    scripts: typing.Iterable[str] = (),
    includes: typing.Iterable[str] = (),
    packages: typing.Iterable[str] = (),
) -> ModuleGraph: ...
def find_modules(
    scripts: typing.Iterable[str] = (),
    includes: typing.Iterable[str] = (),
    packages: typing.Iterable[str] = (),
    excludes: typing.Iterable[str] = (),
    path: typing.Sequence[str] | None = None,
    debug: int = 0,
) -> ModuleGraph: ...
