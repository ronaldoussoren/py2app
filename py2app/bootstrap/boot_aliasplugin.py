def _run():
    global __file__
    import os, sys, site
    sys.frozen = 'macosx_plugin'

    if 'ARGVZERO' in os.environ:
        argv0 = os.path.basename(os.environ['ARGVZERO'])
    else:
        argv0 = None
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)

    sys.argv[0] = __file__ = script
    with open(script, 'rU') as fp:
        source = fp.read() + "\n"

    exec(compile(source, script, 'exec'), globals(), globals())


