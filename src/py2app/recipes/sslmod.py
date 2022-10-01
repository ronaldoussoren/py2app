import io
import os
import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo

PRESCRIPT = """
def _setup_openssl():
    import os
    resourcepath = os.environ["RESOURCEPATH"]
    os.environ["%(openssl_cafile_env)s"] = os.path.join(
        resourcepath, "openssl.ca", "%(cafile_path)s")
    os.environ["%(openssl_capath_env)s"] = os.path.join(
        resourcepath, "openssl.ca", "%(capath_path)s")

_setup_openssl()
"""


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("ssl")
    if m is None or m.filename is None:
        return None

    import ssl

    datafiles = []
    paths = ssl.get_default_verify_paths()
    if paths.cafile is not None:
        datafiles.append(paths.cafile)
        cafile_path = os.path.basename(paths.cafile)
    else:
        cafile_path = "no-such-file"

    if paths.capath is not None:
        datafiles.append(paths.capath)
        capath_path = os.path.basename(paths.capath)
    else:
        capath_path = "no-such-file"

    prescript = PRESCRIPT % {
        "openssl_cafile_env": paths.openssl_cafile_env,
        "openssl_capath_env": paths.openssl_capath_env,
        "cafile_path": cafile_path,
        "capath_path": capath_path,
    }

    return {
        "resources": [("openssl.ca", datafiles)],
        "prescripts": [io.StringIO(prescript)],
    }
