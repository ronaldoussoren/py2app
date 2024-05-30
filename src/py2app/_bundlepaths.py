import dataclasses
import pathlib

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
    dylib: pathlib.Path


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
        dylib=root / "Contents/Frameworks/lib",
    )
