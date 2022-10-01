import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    # As of Python 3.6 the sysconfig module
    # dynamically imports a module using the
    # __import__ function.
    m = mf.findNode("sysconfig")
    if m is not None:
        import sysconfig

        mf.import_hook(sysconfig._get_sysconfigdata_name(), m)  # type: ignore

    return None
