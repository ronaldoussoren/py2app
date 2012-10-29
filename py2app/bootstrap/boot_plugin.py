def _run():
    global __file__
    import os, sys, site
    sys.frozen = 'macosx_plugin'
    base = os.environ['RESOURCEPATH']

    if 'ARGVZERO' in os.environ:
        argv0 = os.path.basename(os.environ['ARGVZERO'])
    else:
        argv0 = None
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)

    path = os.path.join(base, script)
    __file__ = path
    with open(path, 'rU') as fp:
        source = fp.read()
    exec(compile(source, path, 'exec'), globals(), globals())

