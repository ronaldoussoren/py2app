"""
Interaction with macholib.MachOStandalone

XXX: Longer term this needs a complete rewrite, but
that requires rewriting macholib as well.
"""

import contextlib
import pathlib
import shutil
import typing

import macholib.MachO
from macholib.util import in_system_path

from ._config import BundleOptions
from ._modulegraph import ModuleGraph
from .progress import Progress
from .util import iter_platform_files


@contextlib.contextmanager
def writable(path: pathlib.Path):
    mode = path.stat().st_mode

    path.chmod(mode | 0o200)
    try:
        yield
    finally:
        path.chmod(mode)


def rewrite_headers(path: pathlib.Path, m: macholib.MachO.MachO) -> None:
    with writable(path):
        with path.open("rb+") as fp:
            for _header in m.headers:
                fp.seek(0)
                m.write(fp)
            fp.seek(0, 2)
            fp.flush()


def macho_standalone(
    root: pathlib.Path,
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
    # - Recipe interaction
    # - 'Excludes'
    # - 'Includes'
    # - Fill 'todo' based on the module graph (Extension modules),
    #   plus the load commands (should make recipe interaction
    #   easier)
    todo = {pathlib.Path(p) for p in iter_platform_files(root)}
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

                filename = pathlib.Path(filename)
                if not filename.exists():
                    progress.error(
                        f"Required MachO library file {filename} does not exist"
                    )
                    continue

                # XXX: Needs adjustments for frameworks
                target_path = root / "Contents/Frameworks" / filename.name
                rpath = f"@rpath/{filename.name}"

                changes[str(filename)] = rpath

                if target_path not in seen and target_path not in todo:
                    progress.update(task_id, total=len(todo) + len(seen))
                    if not target_path.exists():
                        shutil.copy2(filename, target_path, follow_symlinks=False)
                        todo.add(target_path)

        def changefunc(name):
            result = changes.get(name, name)  # noqa: B023
            return result

        changed = m.rewriteLoadCommands(changefunc)
        if changed:
            rewrite_headers(current, m)

    progress.update(task_id, current=None)
    progress.update(task_id, current="")
    progress.task_done(task_id)
