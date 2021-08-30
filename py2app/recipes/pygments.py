import os


def check(cmd, mf):
    m = mf.findNode("pygments")
    if m is None or m.filename is None:
        return None

    base = os.path.dirname(m.packagepath[0]) + os.sep
    includes = []
    for parent, dirs, files in os.walk(m.packagepath[0]):
        pkg = parent.split(base)[1]
        for file in files:
            if file.endswith('.py'):
                includes.append(os.path.join(pkg, file[:-3]).replace(os.sep, '.'))

    return {"includes": includes}
