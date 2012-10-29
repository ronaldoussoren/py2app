def _run():
    global __file__
    import os, sys, site
    sys.frozen = 'macosx_app'

    argv0 = os.path.basename(os.environ['ARGVZERO'])
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)

    sys.argv[0] = __file__ = script
    with open(script, 'rU') as fp:
        source = fp.read() + "\n"

    exec(compile(source, script, 'exec'), globals(), globals())

