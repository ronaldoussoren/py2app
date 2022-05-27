import importlib.resources
import os
import plistlib
import shutil
import sys

from py2app.util import make_exec, makedirs, mergecopy, mergetree, skipscm

from . import apptemplate


def create_appbundle(
    destdir,
    name,
    extension=".app",
    platform="MacOS",
    copy=mergecopy,
    mergetree=mergetree,
    condition=skipscm,
    plist=None,
    arch=None,
    use_old_sdk=False,
    redirect_stdout=False,
    progress=None,
):
    if plist is None:
        plist = {}

    kw = apptemplate.plist_template.infoPlistDict(
        plist.get("CFBundleExecutable", name), plist
    )
    app = os.path.join(destdir, kw["CFBundleName"] + extension)
    if os.path.exists(app):
        # Remove any existing build artifacts to ensure that
        # we're getting a clean build
        shutil.rmtree(app)
    contents = os.path.join(app, "Contents")
    resources = os.path.join(contents, "Resources")
    platdir = os.path.join(contents, platform)
    dirs = [contents, resources, platdir]
    plist = {}
    plist.update(kw)
    plistPath = os.path.join(contents, "Info.plist")
    if os.path.exists(plistPath):
        with open(plistPath, "rb") as fp:
            contents = plistlib.load(fp)

            if plist != contents:
                for d in dirs:
                    shutil.rmtree(d, ignore_errors=True)
    for d in dirs:
        makedirs(d)

    with open(plistPath, "wb") as fp:
        if hasattr(plistlib, "dump"):
            plistlib.dump(plist, fp)
        else:
            plistlib.writePlist(plist, fp)

    srcmain = apptemplate.setup.main(
        arch=arch, redirect_asl=redirect_stdout, use_old_sdk=use_old_sdk
    )
    destmain = os.path.join(platdir, kw["CFBundleExecutable"])

    with open(os.path.join(contents, "PkgInfo"), "w") as fp:
        fp.write(kw["CFBundlePackageType"] + kw["CFBundleSignature"])

    progress.trace(f"Copy {srcmain!r} -> {destmain!r}")
    copy(srcmain, destmain)
    make_exec(destmain)
    with importlib.resources.path(apptemplate.__name__, "lib") as p:
        mergetree(
            str(p),
            resources,
            condition=condition,
            copyfn=copy,
        )
    return app, plist


if __name__ == "__main__":
    create_appbundle("build", sys.argv[1])
