import sys

SCRIPT_MAP: "dict[str, str]"
DEFAULT_SCRIPT: str


def _run() -> None:
    global __file__
    import marshal
    import site  # noqa: F401
    import zipfile

    sys.frozen = "macosx_app"  # type: ignore
    base = sys.py2app_bundle_resources

    argv0 = sys.py2app_argv0.rsplit("/", 1)[-1]
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)  # noqa: F821

    path = f"{base}/python-libraries.zip/bundle-scripts/{script}"
    sys.argv[0] = __file__ = path

    zf = zipfile.ZipFile(f"{base}/python-libraries.zip", "r")
    source = zf.read(f"bundle-scripts/{script}")

    exec(marshal.loads(source[16:]), globals(), globals())
