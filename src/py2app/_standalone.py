"""
The main entry point in this module is "macho_standalone", which
copies dependent Mach-O libraries into a bundle.
"""

# XXX: This likely needs work to properly handle @rpath, @loader_path and
#      @executable_path. In particular, the code needs to keep track
#      of the source of Mach-O files to properly resolve such relative paths
#      to find the referenced files.
#
# XXX: Longer term create "macholib2" with a modern interface.

__all__ = ("macho_standalone",)

import contextlib
import os
import pathlib
import shutil
import sys
import typing

import macholib.MachO
from macholib.util import in_system_path, is_platform_file

from ._bundlepaths import BundlePaths
from ._config import BundleOptions
from ._modulegraph import ModuleGraph
from .progress import Progress


def iter_platform_files(path: pathlib.Path) -> typing.Iterator[str]:
    """
    Yield all Mach-O files in the tree starting at *path*
    """
    # XXX: Switch to path.walk() when dropping support
    #      for 3.11.
    for root_str, _dirs, files in os.walk(path):
        root = pathlib.Path(root_str)
        for fn in files:
            current = root / fn
            if current.is_symlink():
                continue

            if is_platform_file(str(current)):
                yield current


@contextlib.contextmanager
def writable(path: pathlib.Path):
    """
    Contextmanager that temporarily makes a file writable
    """
    mode = path.stat().st_mode

    path.chmod(mode | 0o200)
    try:
        yield
    finally:
        path.chmod(mode)


def rewrite_headers(path: pathlib.Path, macho: macholib.MachO.MachO) -> None:
    """
    Rewrite the Mach-O headers for *path* using the (updated) information
    in *macho*.
    """
    with writable(path):
        with path.open("rb+") as fp:
            for _header in macho.headers:
                fp.seek(0)
                macho.write(fp)
            fp.seek(0, 2)
            fp.flush()


def copy_library(src: pathlib.Path, dst: pathlib.Path) -> None:
    """
    Copy a shared library from *src* to *dst*
    """
    shutil.copy2(src, dst, follow_symlinks=False)
    os.chmod(dst, 0o755)


def copy_framework(
    src: pathlib.Path, dst: pathlib.Path, version: str = "Current"
) -> None:
    """
    Copy a framework at *src* to the folder *dst*, only including the specified version
    """
    if src.suffix != ".framework":
        raise RuntimeError("{src} is not a framework")

    if version == "Current":
        version = (src / "Versions/Current").readlink().name

    dst = dst / src.name
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "Versions").mkdir(parents=True)
    (dst / "Versions/Current").symlink_to(version)

    dst = dst / "Versions" / version
    src = src / "Versions" / version

    shutil.copytree(src, dst)


def is_framework_path(path: pathlib.Path) -> bool:
    """
    Return true iff *path* is the main library of a framework
    """
    for p in path.parents:
        if p.suffix == ".framework":
            if p.stem == path.name:
                return True
    return False


def framework_info(path: pathlib.Path) -> typing.Tuple[pathlib.Path, str]:
    """
    Given *path* located in a framework return the root of the framework
    directory and the version of the framework used.
    """
    version = "Current"
    last: typing.Optional[pathlib.Path] = None
    for p in path.parents:
        if p.name == "Versions":
            assert isinstance(last, pathlib.Path)
            version = last.name
        elif p.suffix == ".framework":
            assert version != "Current"
            return p, version

        last = p

    raise RuntimeError(f"Cannot determine framework info for {path}")


def macho_standalone(
    paths: BundlePaths,
    graph: ModuleGraph,
    bundle: BundleOptions,
    ext_map: typing.Dict[pathlib.Path, pathlib.Path],
    progress: Progress,
) -> None:
    """
    Integrate dependent shared libraries into the bundle.

    This will:
        - Copy shared libraries into the 'Frameworks' directory
          of the bundle;
        - If the shared library is a framework: copy the right
          bits of a framework into the bundle (with hooks for
          recipes!)
        - Set the link path in load commands to a path starting
          with '@rpath'
    """
    # XXX:
    # - 'Excludes'
    # - 'Includes'
    #
    # XXX: Recipe interaction
    #
    # XXX: Fill 'todo' based on the module graph (Extension modules),
    #   plus the load commands (should make recipe interaction
    #   easier) [Maybe, current code works just fine for now]
    #
    # XXX: What if "Python.framework" is in "includes" or "excludes"?
    # XXX: Logic for dealing with "excludes"
    include = {pathlib.Path(p) for p in bundle.macho_include}
    # exclude = {pathlib.Path(p) for p in bundle.macho_exclude}

    for fn in include:
        if fn.stem == ".framework":
            copy_framework(fn, paths.framework / fn.name)

        else:
            copy_library(fn, paths.framework / fn.name)

    todo = set(iter_platform_files(paths.root))
    seen = set()
    task_id = progress.add_task("Copy MachO dependencies", count=len(todo))

    while todo:
        current = todo.pop()
        progress.step_task(task_id)
        progress.update(task_id, current=current)

        seen.add(current)
        m = macholib.MachO.MachO(str(current))
        changes = {str(current): f"@rpath/{current.name}"}
        for header in m.headers:
            for _idx, _name, filename in header.walkRelocatables():
                if in_system_path(filename):
                    continue

                if filename.startswith("@loader_path/"):
                    filename = pathlib.Path(current.parent / filename.partition("/")[2])
                    if not filename.exists():
                        progress.error(
                            f"Required MachO library file {filename} does not exist"
                        )
                        continue
                    continue

                filename = pathlib.Path(filename)

                if not filename.exists():
                    progress.error(
                        f"Required MachO library file {filename} does not exist"
                    )
                    continue

                if is_framework_path(filename):
                    fwk, version = framework_info(filename)
                    rpath = f"@rpath/{fwk.name}/Versions/{version}/{fwk.stem}"

                    if str(fwk / "Versions" / version) == sys.base_prefix:
                        # Python framework, perform a minimal copy to avoid including
                        # the entire standard library.
                        #
                        # The code copies the embedded Python library as if
                        # it were a libpython.dylib.
                        target_path = paths.framework / f"libpython{version}.dylib"
                        rpath = f"@rpath/{target_path.name}"

                        changes[str(filename)] = rpath

                        if target_path not in seen and target_path not in todo:
                            todo.add(target_path)
                            progress.update(task_id, total=len(todo) + len(seen))
                            copy_library(filename, target_path)

                        continue

                    changes[str(filename)] = rpath

                    if not (fwk / "Versions" / version).is_dir():
                        copy_framework(fwk, paths.framework, version)
                        for p in iter_platform_files(paths.root):
                            if p not in seen and p not in todo:
                                todo.add(p)
                                progress.update(task_id, total=len(todo) + len(seen))

                else:
                    target_path = paths.framework / filename.name
                    rpath = f"@rpath/{filename.name}"

                    changes[str(filename)] = rpath

                    if target_path not in seen and target_path not in todo:
                        todo.add(target_path)
                        progress.update(task_id, total=len(todo) + len(seen))
                        copy_library(filename, target_path)

        def changefunc(name):
            result = changes.get(name, name)  # noqa: B023
            return result

        changed = m.rewriteLoadCommands(changefunc)
        if changed:
            rewrite_headers(current, m)

    progress.update(task_id, current=None)
    progress.update(task_id, current="")
    progress.task_done(task_id)
