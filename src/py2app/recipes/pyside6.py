import glob
import importlib.resources
import io
import os
import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    name = "PySide6"
    m = mf.findNode(name)
    if m is None or m.filename is None:
        return None

    try:
        from PySide6 import QtCore  # type: ignore
    except ImportError:
        print("WARNING: macholib found PySide6, but cannot import")
        return {}

    plugin_dir = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PluginsPath)

    resource_data = importlib.resources.read_text("py2app.recipes", "qt.conf")
    resource_fp = io.StringIO(resource_data)
    resource_fp.name = "qt.conf"

    resources: typing.Sequence[
        typing.Union[
            str, typing.Tuple[str, typing.Sequence[typing.Union[str, typing.IO[str]]]]
        ]
    ]
    resources = [("", [resource_fp])]
    for item in cmd.qt_plugins if cmd.qt_plugins is not None else ():
        if "/" not in item:
            item = item + "/*"

        if "*" in item:
            for path in glob.glob(os.path.join(plugin_dir, item)):
                rel_path = path[len(plugin_dir) :]  # noqa: E203
                resources.append((os.path.dirname("qt_plugins" + rel_path), [path]))
        else:
            resources.append(
                (
                    os.path.dirname(os.path.join("qt_plugins", item)),
                    [os.path.join(plugin_dir, item)],
                )
            )

    # PySide dumps some of its shared files
    # into /usr/lib, which is a system location
    # and those files are therefore not included
    # into the app bundle by default.
    from macholib.util import NOT_SYSTEM_FILES

    for fn in os.listdir("/usr/lib"):
        add = False
        if fn.startswith("libpyside6-python"):
            add = True
        elif fn.startswith("libshiboken6-python"):
            add = True
        if add:
            NOT_SYSTEM_FILES.append(os.path.join("/usr/lib", fn))

    mf.import_hook("PySide6.support", m, ["*"])
    mf.import_hook("PySide6.support.signature", m, ["*"])
    mf.import_hook("PySide6.support.signature.lib", m, ["*"])
    mf.import_hook("PySide6.support.signature.typing", m, ["*"])

    return {"resources": resources, "packages": ["PySide6"]}
