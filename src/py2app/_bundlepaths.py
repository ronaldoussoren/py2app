import dataclasses
import pathlib
import sys

from ._config import BuildType


@dataclasses.dataclass(frozen=True)
class BundlePaths:
    root: pathlib.Path
    resources: pathlib.Path
    main: pathlib.Path
    pylib_zipped: pathlib.Path
    extlib: pathlib.Path
    pylib: pathlib.Path


def bundle_paths(root: pathlib.Path, build_type: BuildType) -> BundlePaths:
    lib = root / "Contents/Resources/lib"

    if build_type == BuildType.SEMI_STANDALONE:
        pylib_zipped = lib / ("python%d.%d/site-packages.zip" % (sys.version_info[:2]))
    else:
        pylib_zipped = lib / ("python%d%d.zip" % (sys.version_info[:2]))

    return BundlePaths(
        root=root / "Contents",
        resources=root / "Contents/Resources",
        main=root / "Contents/MacOS",
        pylib_zipped=pylib_zipped,
        pylib=lib / "site-packages",
        extlib=lib / "lib-dynload",
    )
