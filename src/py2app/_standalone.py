"""
Interaction with macholib.MachOStandalone

XXX: Longer term this needs a complete rewrite, but
that requires rewriting macholib as well.
"""

import pathlib
import typing
from os import sep as PATH_SEP

import macholib.MachO
from macholib.MachOStandalone import MachOStandalone

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
        *,
        appbuilder,  # XXX
        ext_dir: pathlib.Path,
        copyexts,  # XXX
        base: pathlib.Path,
        dest: typing.Optional[pathlib.Path] = None,
        env: typing.Optional[typing.Dict[str, str]] = None,
        executable_path: typing.Optional[pathlib.Path] = None,
    ) -> None:
        super().__init__(
            str(base),
            str(dest) if dest is not None else None,
            env,
            str(executable_path) if executable_path is not None else None,
        )
        self.appbuilder = appbuilder
        self.ext_map: typing.Dict[pathlib.Path, pathlib.Path] = {}
        for e in copyexts:
            assert e.identifier is not None
            assert e.filename is not None
            fn = ext_dir / (
                e.identifier.replace(".", PATH_SEP) + pathlib.Path(e.filename).suffix
            )
            self.ext_map[fn] = pathlib.Path(e.filename).parent

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
        dst_path = self.dest / src_path.name

        if src_path.is_symlink():
            dst_path = self.dest / src_path.resolve().name

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

        else:
            dst_path = self.dest / src_path.name

        self.ext_map[dst_path] = src_path.parent

        # XXX:
        # 1. Should use Path arguments here
        # 2. Too much indirection!
        return self.appbuilder.copy_dylib(str(src_path), str(dst_path))

    def copy_framework(self, info: _FrameworkInfo) -> str:
        destfn = self.appbuilder.copy_framework(info, self.dest)
        dest = self.dest / (info["shortname"] + ".framework")
        self.pending.append((destfn, iter_platform_files(str(dest))))
        return destfn
