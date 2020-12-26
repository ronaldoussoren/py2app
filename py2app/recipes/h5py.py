def check(cmd, mf):
    m = mf.findNode("h5py")
    if m is None or m.filename is None:
        return None

    # h5py is written in Cython and has
    # "import" dependencies between C
    # extensions
    return {"packages": ["h5py"]}
