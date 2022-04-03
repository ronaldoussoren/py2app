import sys
import os


def check(cmd, mf):
    m = mf.findNode("pkg_resources")
    if m is None or m.filename is None:
        return None

    if m.filename.endswith("__init__.py"):
        vendor_dir = os.path.join(os.path.dirname(m.filename), "_vendor")
    else:
        vendor_dir = os.path.join(m.filename, "_vendor")

    expected_missing_imports = {
        "__main__.__requires__",
    }

    if os.path.exists(vendor_dir):
        for topdir, dirs, files in os.walk(vendor_dir):
            for fn in files:
                if fn in ("__pycache__", "__init__.py"): continue

                relnm = os.path.relpath(os.path.join(topdir, fn), vendor_dir)
                if relnm.endswith(".py"):
                    relnm = relnm[:-3]
                relnm = relnm.replace("/", ".")

                if fn.endswith(".py"):
                    mf.import_hook("pkg_resources._vendor." + relnm, m, ["*"])
                    expected_missing_imports.add("pkg_resources.extern." + relnm)
            for dn in dirs:
                if not os.path.exists(os.path.join(topdir, dn, "__init__.py")):
                    continue
                relnm = os.path.relpath(os.path.join(topdir, dn), vendor_dir)
                relnm = relnm.replace("/", ".")

                mf.import_hook("pkg_resources._vendor." + relnm, m, ["*"])
                expected_missing_imports.add("pkg_resources.extern." + relnm)

        mf.import_hook("pkg_resources._vendor", m)

    if sys.version[0] != 2:
        expected_missing_imports.add("__builtin__")

    return {"expected_missing_imports": expected_missing_imports}
