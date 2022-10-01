import distutils.sysconfig
import distutils.util
import os
import re
import typing

gPreBuildVariants = [
    {
        "name": "main-universal2",
        "target": "10.9",
        "cflags": "-g -arch arm64 -arch x86_64",
        "cc": "/usr/bin/clang",
    },
    {
        "name": "main-arm64",
        "target": "10.16",
        "cflags": "-g -arch arm64",
        "cc": "/usr/bin/clang",
    },
    {
        "name": "main-x86_64",
        "target": "10.5",
        "cflags": "-arch x86_64 -g",
        "cc": "clang",
    },
]


def main(buildall: bool = False, arch: typing.Optional[str] = None) -> str:
    basepath = os.path.dirname(__file__)
    builddir = os.path.join(basepath, "prebuilt")
    if not os.path.exists(builddir):
        os.makedirs(builddir)
    src = os.path.join(basepath, "src", "main.m")

    cfg = distutils.sysconfig.get_config_vars()

    BASE_CFLAGS = cfg["CFLAGS"]
    assert isinstance(BASE_CFLAGS, str)
    BASE_CFLAGS = BASE_CFLAGS.replace("-dynamic", "")
    BASE_CFLAGS += " -bundle -framework Foundation -framework AppKit"
    while True:
        x = re.sub(r"-arch\s+\S+", "", BASE_CFLAGS)
        if x == BASE_CFLAGS:
            break
        BASE_CFLAGS = x

    while True:
        x = re.sub(r"-isysroot\s+\S+", "", BASE_CFLAGS)
        if x == BASE_CFLAGS:
            break
        BASE_CFLAGS = x

    if arch is None:
        arch = distutils.util.get_platform().split("-")[-1]

    name = "main-" + arch
    root = None

    if buildall:
        for entry in gPreBuildVariants:
            if (not buildall) and entry["name"] != name:
                continue

            dest = os.path.join(builddir, entry["name"])
            if not os.path.exists(dest) or (
                os.stat(dest).st_mtime < os.stat(src).st_mtime
            ):
                if root is None:
                    fp = os.popen("xcode-select -print-path", "r")
                    root = fp.read().strip()
                    fp.close()

                print("rebuilding %s" % (entry["name"]))

                CC = entry["cc"]
                CFLAGS = (
                    BASE_CFLAGS + " " + entry["cflags"].replace("@@XCODE_ROOT@@", root)
                )
                os.environ["MACOSX_DEPLOYMENT_TARGET"] = entry["target"]
                os.system('"%(CC)s" -o "%(dest)s" "%(src)s" %(CFLAGS)s' % locals())

    dest = os.path.join(builddir, "main-" + arch)

    return dest


if __name__ == "__main__":
    main(buildall=True)
