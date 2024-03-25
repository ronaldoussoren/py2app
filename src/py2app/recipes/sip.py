"""
Py2app support for project using sip, which basically means PyQt and wrappers
for other Qt-based libraries.

This will include all C modules that might be used when you import a package
using sip because we have no way to fine-tune this.

The problem with SIP is that all inter-module dependencies (for example from
PyQt4.Qt to PyQt4.QtCore) are handled in C code and therefore cannot be
detected by the python code in py2app).
"""

import glob
import importlib.resources
import io
import os
import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


class Sip:
    def __init__(self) -> None:
        self.packages: typing.Optional[typing.Set[str]] = None
        self.plugin_dir: typing.Optional[str] = None

    def config(self) -> typing.Set[str]:
        if self.packages is not None:
            print("packages", self.packages)
            return self.packages

        import os

        import sipconfig  # type: ignore

        try:
            from PyQt4 import pyqtconfig  # type: ignore

            cfg = pyqtconfig.Configuration()
            assert cfg.qt_dir is not None
            qtdir = cfg.qt_lib_dir
            sipdir = os.path.dirname(cfg.pyqt_mod_dir)
            self.plugin_dir = os.path.join(cfg.qt_dir, "plugins")
        except ImportError:
            from PyQt5.QtCore import QLibraryInfo  # type: ignore

            qtdir = QLibraryInfo.location(QLibraryInfo.LibrariesPath)
            self.plugin_dir = QLibraryInfo.location(QLibraryInfo.PluginsPath)
            sipdir = os.path.dirname(sipconfig.__file__)

        if not os.path.exists(qtdir):
            print("sip: Qtdir %r does not exist" % (qtdir))
            # half-broken installation? ignore.
            raise ImportError

        # Qt is GHETTO!
        # This looks wrong, setting DYLD_LIBRARY_PATH should not be needed!
        dyld_library_path = os.environ.get("DYLD_LIBRARY_PATH", "").split(":")

        if qtdir not in dyld_library_path:
            dyld_library_path.insert(0, qtdir)
            os.environ["DYLD_LIBRARY_PATH"] = ":".join(dyld_library_path)

        self.packages = set()

        for fn in os.listdir(sipdir):
            fullpath = os.path.join(sipdir, fn)
            if os.path.isdir(fullpath):
                self.packages.add(fn)
                if fn in ("PyQt4", "PyQt5"):
                    # PyQt4 and later has a nested structure, also import
                    # subpackage to ensure everything get seen.
                    for sub in os.listdir(fullpath):
                        if ".py" not in sub:
                            self.packages.add(
                                "{}.{}".format(fn, sub.replace(".so", ""))
                            )

        print(f"sip: packages: {self.packages}")

        return self.packages

    def check(
        self, cmd: "build_app.py2app", mf: ModuleGraph
    ) -> typing.Optional[RecipeInfo]:
        try:
            packages = self.config()
        except ImportError:
            return None

        if "PyQt4.uic" in packages:
            # PyQt4.uic contains subpackages with python 2 and python 3
            # support. Exclude the variant that won't be ussed, this avoids
            # compilation errors on Python 2 (because some of the Python 3
            # code is not valid Python 2 code)
            ref = "PyQt4.uic.port_v2"

        if "PyQt5.uic" in packages:
            # ditto
            ref = "PyQt5.uic.port_v2"

            # Exclude...
            mf.lazynodes[ref] = None

        for pkg in packages:
            m = mf.findNode(pkg)
            if m is not None and m.filename is not None:
                break

        else:
            print("sip: No sip package used in application")
            return None

        mf.import_hook("sip", m)
        m = mf.findNode("sip")
        # naive inclusion of ALL sip packages
        # stupid C modules.. hate hate hate
        for pkg in packages:
            try:
                mf.import_hook(pkg, m)
            except ImportError as exc:
                print(f"WARNING: ImportError in sip recipe ignored: {exc}")

        if mf.findNode("PyQt4") is not None or mf.findNode("PyQt5") is not None:
            resource_data = importlib.resources.read_text("py2app.recipes", "qt.conf")
            resource_fp = io.StringIO(resource_data)
            resource_fp.name = "qt.conf"

            resources: typing.Sequence[
                typing.Union[
                    str,
                    typing.Tuple[
                        str, typing.Sequence[typing.Union[str, typing.IO[str]]]
                    ],
                ]
            ]
            resources = [("", [resource_fp])]

            for item in cmd.qt_plugins if cmd.qt_plugins is not None else ():
                if "/" not in item:
                    item = item + "/*"

                if "*" in item:
                    assert isinstance(self.plugin_dir, str)
                    for path in glob.glob(os.path.join(self.plugin_dir, item)):
                        rel_path = path[len(self.plugin_dir) :]  # noqa: E203
                        resources.append(
                            (os.path.dirname("qt_plugins" + rel_path), [path])
                        )
                else:
                    assert self.plugin_dir is not None
                    resources.append(
                        (
                            os.path.dirname(os.path.join("qt_plugins", item)),
                            [os.path.join(self.plugin_dir, item)],
                        )
                    )

            return {"resources": resources}

        return {}


check = Sip().check
