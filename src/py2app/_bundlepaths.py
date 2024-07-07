import dataclasses
import pathlib
import typing

from ._config import BuildType


@dataclasses.dataclass(frozen=True)
class BundlePaths:
    root: pathlib.Path
    bin: pathlib.Path  # noqa: A003
    resources: pathlib.Path
    main: pathlib.Path
    pylib_zipped: pathlib.Path
    extlib: pathlib.Path
    pylib: pathlib.Path
    framework: pathlib.Path

    def all_directories(self) -> typing.List[pathlib.Path]:
        """
        Return all directories for the bundle paths
        """
        return [
            self.root,
            self.bin,
            self.resources,
            self.main,
            self.pylib,
            self.extlib,
            self.framework,
        ]


def bundle_paths(root: pathlib.Path, build_type: BuildType) -> BundlePaths:
    # See doc/bundle-structure.rst, section "Python Locations"
    return BundlePaths(
        root=root / "Contents",
        bin=root / "Contents/Resources/bin",
        resources=root / "Contents/Resources",
        main=root / "Contents/MacOS",
        pylib_zipped=root / "Contents/Resources/python-libraries.zip",
        pylib=root / "Contents/Resources/python-libraries",
        extlib=root / "Contents/Resources/lib-dynload",
        framework=root / "Contents/Frameworks",
    )
