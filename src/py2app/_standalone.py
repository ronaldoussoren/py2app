"""
Interaction with macholib.MachOStandalone

XXX: Longer term this needs a complete rewrite, but
that requires rewriting macholib as well.
"""

import pathlib
import shutil
import typing

import macholib.MachO
from macholib.MachOStandalone import MachOStandalone

from ._config import BuildType
from ._modulegraph import ModuleGraph
from .progress import Progress
from .util import iter_platform_files


class _FrameworkInfo(typing.TypedDict):
    # XXX: should be imported...
    location: str
    name: str
    shortname: str
    version: str
    suffix: str


class PythonStandalone(MachOStandalone):
    def __init__(
        self,
        base: pathlib.Path,
        graph: ModuleGraph,
        build_type: BuildType,
        ext_map: typing.Dict[pathlib.Path, pathlib.Path],
        progress: Progress,
    ) -> None:
        env = None
        super().__init__(
            base=str(base),
            dest=None,
            env=env,
            executable_path=str(base / "Contents/MacOS"),
        )
        self.ext_map: typing.Dict[pathlib.Path, pathlib.Path] = ext_map
        self.progress = progress
        self.task_id = progress.add_task("Copy MachO dependencies", count=None)

    def run(self):
        super().run()
        self.progress.task_done(self.task_id)

    def update_node(
        self, m: typing.Optional[macholib.MachO.MachO]
    ) -> typing.Optional[macholib.MachO.MachO]:
        if isinstance(m, macholib.MachO.MachO):
            assert m.filename is not None
            file_path = pathlib.Path(m.filename)
            if file_path in self.ext_map:
                m.loader_path = str(self.ext_map[file_path])
        return m

    def copy_dylib(self, src: str) -> str:
        src_path = pathlib.Path(src)
        dst_path = pathlib.Path(self.dest) / src_path.name

        self.progress.update(self.task_id, current=f"{src_path} -> {dst_path}")
        self.progress.step_task(self.task_id)

        if src_path.resolve() == dst_path.resolve():
            return

        if dst_path.exists():
            return

        if src_path.is_symlink():
            # Ensure that the original name also exists, avoids problems when
            # the filename is used from Python (see issue #65)
            #
            # NOTE: The if statement checks that the target link won't
            #       point to itself, needed for systems like homebrew that
            #       store symlinks in "public" locations that point to
            #       files of the same name in a per-package install location.
            link_dest = self.dest / src_path.name
            if link_dest.name != dst_path.name:
                link_dest.symlink_to(dst_path.name)

        self.ext_map[dst_path] = src_path.parent

        # XXX:
        # 1. Should use Path arguments here
        # 2. Too much indirection!
        shutil.copy2(src_path, dst_path, follow_symlinks=False)
        return str(dst_path)

    def copy_framework(self, info: _FrameworkInfo) -> str:
        destfn = self.appbuilder.copy_framework(info, self.dest)
        dest = self.dest / (info["shortname"] + ".framework")
        self.pending.append((destfn, iter_platform_files(str(dest))))
        return destfn
