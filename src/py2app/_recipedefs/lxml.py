# XXX: Check if this is still relevant
import typing

from modulegraph2 import BaseNode

from .._config import RecipeOptions
from .._modulegraph import ModuleGraph
from .._recipes import recipe

DEPS: typing.List[typing.Tuple[str, typing.List[str]]] = [
    ("lxml.etree", ["lxml._elementpath", "os.path", "re", "gzip", "io"]),
    ("lxml.objectivy", ["copyreg"]),
]


@recipe("lxml", distribution="lxml", modules=["lxml"])
def lxml(graph: ModuleGraph, options: RecipeOptions) -> None:
    """
    Recipe for `lxml <https://pypi.org/project/lxml>`_
    """

    for mod, to_import in DEPS:
        m = graph.find_node(mod)
        if not isinstance(m, BaseNode) or m.filename is None:
            continue

        for i in to_import:
            graph.import_module(m, i)

    m = graph.find_node("lxml.isoschematron")
    if m is not None:
        graph.mark_zipunsafe(m)
