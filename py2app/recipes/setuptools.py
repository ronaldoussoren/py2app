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
        for nm in os.listdir(vendor_dir):
            if nm in ("__pycache__", "__init__.py"): continue
            if nm.endswith(".py"):
                mf.import_hook("pkg_resources._vendor." + (nm[:-3]), m, ["*"])
                expected_missing_imports.add("pkg_resources.extern." + (nm[:3]))
            elif os.path.isdir(os.path.join(vendor_dir)):
                mf.import_hook("pkg_resources._vendor." + nm, m, ["*"])
                expected_missing_imports.add("pkg_resources.extern." + nm)

        mf.import_hook("pkg_resources._vendor", m)

    #for node in mf.nodes():
    #    if node.name and node.name.startswith("pkg_resources.extern"):
    #        suffix = node.name[len("pkg_resources.extern."):]
    #        mf.import_hook("pkg_resources._vendor." + suffix, node, ["*"])


    if sys.version[0] != 2:
        expected_missing_imports.add("__builtin__")

    return {"expected_missing_imports": expected_missing_imports}
