
def check(cmd, mf):
    m = mf.findNode("black")
    if m is None or m.filename is None:
        return None

    includes = ["610faff656c4cfcbb4a3__mypyc", "blackd", "pathspec"]
    packages = ["black", "blib2to3"]

    return {"includes": includes, "packages": packages}
