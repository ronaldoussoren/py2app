import os
import typing

from modulegraph.modulegraph import MissingModule, ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("PyQt6")
    if m and not isinstance(m, MissingModule):
        try:
            # PyQt6 with sipconfig module, handled
            # by sip recipe
            import sipconfig  # type: ignore  # noqa: F401

            return None

        except ImportError:
            pass

        try:
            import PyQt6  # type: ignore
            from PyQt6.QtCore import QLibraryInfo  # type: ignore
        except ImportError:
            # Dependency in the graph, but PyQt6 isn't
            # installed.
            return None

        qtdir = QLibraryInfo.path(QLibraryInfo.LibraryPath.LibrariesPath)
        assert isinstance(qtdir, str)
        if os.path.relpath(qtdir, os.path.dirname(PyQt6.__file__)).startswith("../"):
            # Qt6's prefix is not the PyQt6 package, which means
            # the "packages" directive below won't include everything
            # needed, and in particular won't include the plugins
            # folder.
            print("System install of Qt6")

            # Ensure that the Qt plugins are copied into the "Contents/plugins" folder,
            # that's where the bundles Qt expects them to be
            pluginspath = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
            assert isinstance(pluginspath, str)
            resources = [("..", [pluginspath])]

        else:
            resources = None

        # All imports are done from C code, hence not visible
        # for modulegraph
        # 1. Use of 'sip'
        # 2. Use of other modules, datafiles and C libraries
        #    in the PyQt5 package.
        try:
            mf.import_hook("sip", m)
        except ImportError:
            mf.import_hook("sip", m, level=1)

        result: RecipeInfo = {"packages": ["PyQt6"]}
        if resources is not None:
            result["resources"] = resources
        return result

    return None
