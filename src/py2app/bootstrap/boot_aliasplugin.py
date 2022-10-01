import sys

SCRIPT_MAP: "dict[str|None, str]"
DEFAULT_SCRIPT: str


def _run() -> None:
    global __file__
    import os
    import site  # noqa: F401

    sys.frozen = "macosx_plugin"  # type: ignore
    base = os.environ["RESOURCEPATH"]

    if "ARGVZERO" in os.environ:
        argv0 = os.path.basename(os.environ["ARGVZERO"])
    else:
        argv0 = None
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)  # noqa: F821

    sys.argv[0] = __file__ = path = os.path.join(base, script)
    with open(path, "rb") as fp:
        source = fp.read() + b"\n"

    exec(compile(source, script, "exec"), globals(), globals())
