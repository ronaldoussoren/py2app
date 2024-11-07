from modulegraph2 import BaseNode

from .._config import RecipeOptions
from .._modulegraph import ModuleGraph
from .._recipes import recipe


@recipe("truststore", distribution="truststore", modules=["truststore"])
def truststore(graph: ModuleGraph, options: RecipeOptions) -> None:
    """
    Recipe for `platformdirs <https://pypi.org/project/platformdirs>`_
    """
    m = graph.find_node("truststore._api")
    if not isinstance(m, BaseNode) or m.filename is None:
        return

    graph.remove_all_edges(m, "truststore._windows")
    graph.remove_all_edges(m, "truststore._openssl")

    # 'inject_into_ssl' can integrate with 3th a number
    # of libraries, those links can be cut to ensure
    # these libraries are only included when the app
    # actually uses them.
    graph.remove_all_edges(m, "urllib3.util.ssl_")
