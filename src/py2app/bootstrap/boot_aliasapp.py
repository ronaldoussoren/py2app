import sys

SCRIPT_MAP: "dict[str, str]"
DEFAULT_SCRIPT: str


def _run() -> None:
    global __file__
    import site  # noqa: F401

    sys.frozen = "macosx_app"  # type: ignore

    argv0 = sys.py2app_argv0.rsplit("/", 1)[-1]
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)  # noqa: F821

    sys.argv[0] = __file__ = script
    with open(script, "rb") as fp:
        source = fp.read() + b"\n"

    exec(compile(source, script, "exec"), globals(), globals())
