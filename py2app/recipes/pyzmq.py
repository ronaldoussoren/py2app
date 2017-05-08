def check(cmd, mf):
    m = mf.findNode('zmq')
    if m is None or m.filename is None:
        return None

    # PyZMQ is a package that contains
    # a shared library. This recipe
    # is mostly a workaround for a bug
    # in py2app: it copies the dylib into
    # the site-packages zipfile and builds
    # a non-functionaly application.
    return dict(
        packages=['zmq']
    )
