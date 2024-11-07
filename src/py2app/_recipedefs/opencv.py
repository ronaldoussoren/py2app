from modulegraph2 import BaseNode

from .._config import RecipeOptions
from .._modulegraph import ModuleGraph
from .._recipes import recipe


@recipe("opencv-python", distribution="opencv-python", modules=["cv2"])
def opencv(graph: ModuleGraph, options: RecipeOptions) -> None:
    """
    Recipe for `opencv-python <https://pypi.org/project/opencv-python>`_
    """

    # The 'cv2.cv2' extension module imports 'numpy', update the
    # graph for this.
    m = graph.find_node("cv2.cv2")
    if not isinstance(m, BaseNode) or m.filename is None:
        return None

    graph.import_module(m, "numpy")
