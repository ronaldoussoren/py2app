import imp
import os
import sys
import types

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
        return imp.load_module(
            fullname, None, os.path.join(pkg_dir, fullname), ("", "", imp.PKG_DIRECTORY)
        )


class Finder:
    def find_module(
        self, fullname: str, path: "list[str]|None" = None
    ) -> "Loader|None":
        if fullname in _path_hooks:  # noqa: F821
            return Loader()
        return None


sys.meta_path.insert(0, Finder())  # type: ignore
