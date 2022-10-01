import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("gcloud")
    if m is None or m.filename is None:
        return None

    # Dependency in package metadata, but
    # no runtime dependency. Explicitly include
    # to ensure that the package metadata for
    # googleapis_common_protos is included.
    return {"includes": ["google.api"]}
