import sys


def check(cmd, mf):
    m = mf.findNode("setuptools")
    if m is None or m.filename is None:
        return None
    for pkg in ["more_itertools", "ordered_set", "packaging", "pyparsing"]:
        mf.import_hook("setuptools._vendor." + pkg, m, ["*"])

    expected_missing_imports = {
        "setuptools.extern.more_itertools",
        "setuptools.extern.ordered_set",
        "setuptools.extern.packaging",
        "setuptools.extern.pyparsing",
    }
    includes = {
        "setuptools.msvc",
    }

    return {"expected_missing_imports": expected_missing_imports, "includes": includes}
