# Set up loader for extension modules in possibly
# zipped packages.
import importlib
import os
import sys
from importlib.abc import MetaPathFinder


class Py2AppExtensionLoader(MetaPathFinder):
    def __init__(self, libdir):
        self._libdir = libdir

    def find_spec(self, fullname, path, target=None):
        ext_path = f"{self._libdir}/{fullname}.so"
        if not os.path.exists(ext_path):
            return None

        loader = importlib.machinery.ExtensionFileLoader(fullname, ext_path)
        return importlib.machinery.ModuleSpec(name=fullname, loader=loader, origin=path)


for p in sys.path:
    if p.endswith("/lib-dynload"):
        sys.meta_path.insert(0, Py2AppExtensionLoader(p))
