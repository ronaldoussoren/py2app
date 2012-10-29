def _run():
    global __file__
    import os, sys, site
    sys.frozen = 'macosx_app'
    base = os.environ['RESOURCEPATH']

    argv0 = os.path.basename(os.environ['ARGVZERO'])
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)

    path = os.path.join(base, script)
    sys.argv[0] = __file__ = path
    with open(path, 'rU') as fp:
        source = fp.read() + "\n"
    exec(compile(source, path, 'exec'), globals(), globals())
