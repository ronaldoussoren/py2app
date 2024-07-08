"""
*BundlePaths* defines the paths to interesting locations
in a  bundle.
"""

import dataclasses
import pathlib
import typing

__all__ = ("BundlePaths", "bundle_paths")


@dataclasses.dataclass(frozen=True)
class BundlePaths:
    """
    Record the paths to interesting bits of a bundle:

    - ``root``: 'Contents' folder;
    - ``bin``:  Location for secondary binaries ("extra_scripts");
    - ``resources``: Root of the resource folder;
    - ``main``: Folder containing the main bundle binary;
    - ``pylib``: Location of Python libraries used that aren't zip safe;
    - ``pylib_zipped``: Location of the zip file containing the Python libraries used;
    - ``extlib``: Location of C extensions with special handling;
    - ``framework``: Location for included native libraries and frameworks.
    """

    root: pathlib.Path
    bin: pathlib.Path  # noqa: A003
    resources: pathlib.Path
    main: pathlib.Path
    pylib: pathlib.Path
    pylib_zipped: pathlib.Path
    extlib: pathlib.Path
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


def bundle_paths(root: pathlib.Path) -> BundlePaths:
    """
    Return a ``BundlePaths`` value for a bundle located at *root*.
    """
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
