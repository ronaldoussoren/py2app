# mypy: ignore-errors

import imp
import os
import sys
import types

from importlib._bootstrap import _exec, _load
from importlib import machinery, util

_path_hooks: "list[str]"


# XXX: Is this function used at all?
def _included_subpackages(packages: "list[str]") -> None:
    for _pkg in packages:
        pass


class Loader:
    def load_module(self, fullname: str) -> types.ModuleType:
        pkg_dir = os.path.join(
            os.environ["RESOURCEPATH"], "lib", "python%d.%d" % (sys.version_info[:2])
        )
        path = os.path.join(pkg_dir, fullname)
        if os.path.isdir(path):
            extensions = (machinery.SOURCE_SUFFIXES[:] +
                          machinery.BYTECODE_SUFFIXES[:])
            for extension in extensions:
                init_path = os.path.join(path, '__init__' + extension)
                if os.path.exists(init_path):
                    path = init_path
                    break
            else:
                raise ValueError('{!r} is not a package'.format(path))
        spec = util.spec_from_file_location(fullname, path, submodule_search_locations=[])
        if fullname in sys.modules:
            return _exec(spec, sys.modules[fullname])
        else:
            return _load(spec)


class Finder:
    def find_module(
        self, fullname: str, path: "list[str]|None" = None
    ) -> "Loader|None":
        if fullname in _path_hooks:  # noqa: F821
            return Loader()
        return None


sys.meta_path.insert(0, Finder())  # type: ignore
