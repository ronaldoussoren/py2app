def _run(*scripts):
    global __file__
    import os, sys, site
    sys.frozen = 'macosx_app'
    base = os.environ['RESOURCEPATH']

    if not scripts:
        import __main__
    for script in scripts:
        path = os.path.join(base, script)
        sys.argv[0] = __file__ = path
        with open(path) as fp:
            source = fp.read() + "\n"
        exec(compile(source, path, 'exec'), globals(), globals())

