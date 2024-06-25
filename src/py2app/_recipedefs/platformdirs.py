from modulegraph2 import ModuleGraph

from .._config import RecipeOptions
from .._recipes import recipe


@recipe("sphinx", distribution="platformdirs", modules=["platformdirs"])
def platformdirs(graph: ModuleGraph, options: RecipeOptions) -> None:
    """
    Recipe for `platformdirs <https://pypi.org/project/platformdirs>`_
    """
    m = graph.find_node("platformdirs")
    if m is None or m.filename is None:
        return None

    # The package init dynamically determines which platform
    # specific submodule to import. Py2app only runs on
    # macOS, so we can hardcode the specific platform module
    # to use.
    graph.import_module(m, "platformdirs.macos")
