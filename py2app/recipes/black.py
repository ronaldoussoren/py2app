import os

from pkg_resources import get_distribution


def check(cmd, mf):
    m = mf.findNode("black")
    if m is None or m.filename is None:
        return None

    egg = get_distribution("black").egg_info
    top = os.path.join(egg, "top_level.txt")

    # These cannot be in zip
    packages = ["black", "blib2to3"]

    # black may include optimized platform specific C extension which has
    # unusual name, e.g. 610faff656c4cfcbb4a3__mypyc; best to determine it from
    # the egg-info/top_level.txt
    with open(top, "r") as f:
        includes = set(f.read().strip().split("\n"))
    includes = list(includes.difference(packages))

    # Missed dependency
    includes.append("pathspec")

    return {"includes": includes, "packages": packages}
