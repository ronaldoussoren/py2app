import os
import plistlib
import shutil
import sys
import typing

if sys.version_info[:2] < (3, 10):
    import importlib_resources
else:
    import importlib.resources as importlib_resources

from . import bundletemplate, progress
from .util import make_exec, make_path, mergecopy, mergetree, skipscm


def create_pluginbundle(
    destdir: typing.Union[str, os.PathLike[str]],
    name: str,
    *,
    progress: progress.Progress,
    extension: str = ".plugin",
    platform: str = "MacOS",
    copy: typing.Callable[[str, str], None] = mergecopy,
    mergetree: typing.Callable[
        [str, str, typing.Callable[[str], bool], typing.Callable[[str, str], None]],
        None,
    ] = mergetree,
    condition: typing.Callable[[str], bool] = skipscm,
    plist: typing.Optional[typing.Dict[str, typing.Any]] = None,
    arch: str = None,
) -> typing.Tuple[str, dict]:
    destpath = make_path(destdir)
    if plist is None:
        plist = {}

    kw = bundletemplate.plist_template.infoPlistDict(
        plist.get("CFBundleExecutable", name), plist
    )
    plugin = destpath / (kw["CFBundleName"] + extension)
    if plugin.exists():
        # Remove any existing build artifacts to ensure
        # we're getting a clean build
        shutil.rmtree(plugin)
    contents = plugin / "Contents"
    resources = contents / "Resources"
    platdir = contents / platform
    dirs = [contents, resources, platdir]
    plist = {}
    plist.update(kw)
    plistPath = contents / "Info.plist"

    for d in dirs:
        progress.trace(f"Create {d}")
        d.mkdir(parents=True, exist_ok=True)

    with open(plistPath, "wb") as fp:
        progress.trace(f"Write {plistPath}")
        plistlib.dump(plist, fp)
    srcmain = bundletemplate.setup.main(arch=arch)
    destmain = platdir / kw["CFBundleExecutable"]
    (contents / "PkgInfo").write_text(
        kw["CFBundlePackageType"] + kw["CFBundleSignature"]
    )

    progress.trace(f"Copy {srcmain!r} -> {destmain!r}")
    copy(srcmain, destmain)
    make_exec(destmain)

    # XXX: Below here some pathlib.Path instances are converted
    # back to strings for compatibility with other code.
    # This will be changed when that legacy code has been updated.
    with importlib_resources.path(bundletemplate.__name__, "lib") as p:
        mergetree(
            str(p),
            str(resources),
            condition,
            copy,
        )
    return str(plugin), plist
