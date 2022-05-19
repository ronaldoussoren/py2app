try:
    from importlib.metadata import distributions # importlib for python 3.9 and later
except ImportError:
    from importlib.metadata import packages_distributions as distributions

def check(cmd, mf):
    m = mf.findNode("black")
    if m is None or m.filename is None:
        return None

    # These cannot be in zip
    packages = {"black", "blib2to3"}

    # black may include optimized platform specific C extension which has
    # unusual name, e.g. 610faff656c4cfcbb4a3__mypyc; extract
    # the name from the list of toplevels.
    includes = set()
    for toplevel, dists in distributions():
        if "black" not in dists:
            continue

        includes.add(toplevel)

    includes -= packages

    # Missed dependency
    includes.add("pathspec")

    # XXX: verify if caller knows how to work with sets
    return {"includes": list(includes), "packages": list(packages)}
