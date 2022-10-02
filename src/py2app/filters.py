import pathlib
import sys

from macholib.util import in_system_path
from modulegraph import modulegraph


def has_filename_filter(module: modulegraph.Node, /) -> bool:
    if isinstance(module, modulegraph.MissingModule):
        return True
    if hasattr(modulegraph, "InvalidRelativeImport") and isinstance(
        module, modulegraph.InvalidRelativeImport
    ):
        return True
    return getattr(module, "filename", None) is not None


def _is_site_path(relpath: pathlib.Path) -> bool:
    return bool(any(x in relpath.parts for x in {"site-python", "site-packages"}))


def not_stdlib_filter(module: modulegraph.Node) -> bool:
    """
    Return False if the module is located in the standard library
    """

    if module.filename is None:
        return True

    prefix = pathlib.Path(sys.prefix).resolve()
    rp = pathlib.Path(module.filename).resolve()

    if rp.is_relative_to(prefix):
        return _is_site_path(rp.relative_to(prefix))

    if (prefix / ".Python").exists():
        # Virtualenv
        v = sys.version_info
        fn = prefix / "lib" / f"python{v[0]}.{v[1]}" / "orig-prefix.txt"

        if fn.exists():
            prefix = pathlib.Path(fn.read_text().strip())
            if rp.is_relative_to(prefix):
                return _is_site_path(rp.relative_to(prefix))

    if hasattr(sys, "base_prefix"):
        # Venv
        prefix = pathlib.Path(sys.base_prefix).resolve()
        if rp.is_relative_to(prefix):
            return _is_site_path(rp.relative_to(prefix))

    return True


def not_system_filter(module: modulegraph.Node) -> bool:
    """
    Return False if the module is located in a system directory
    """
    if module.filename is None:
        return False
    return not in_system_path(module.filename)
