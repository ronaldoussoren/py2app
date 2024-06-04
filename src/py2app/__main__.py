import argparse
import pathlib
import sys

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from . import __version__, _builder, _config, _progress

DESCRIPTION = """\
Build macOS executable bundles, in particular ".app" bundles.

By default this will build fully standalone bundles, that is
applications that can be used on different machines without
installing dependencies.
"""


def parse_arguments(argv):
    parser = argparse.ArgumentParser(
        prog=f"{sys.executable} -mpy2app",
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )

    # XXX: Consider walking up the tree upto to the top of
    # project tree (the directory containing a `.git` directory)
    parser.add_argument(
        "--pyproject-toml",
        "-c",
        dest="pyproject",
        default="./pyproject.toml",
        metavar="FILE",
        type=pathlib.Path,
        help="path to pyproject.toml (default: %(default)s)",
    )
    parser.add_argument(
        "--semi-standalone",
        dest="build_type",
        default=None,
        action="store_const",
        const=_config.BuildType.SEMI_STANDALONE,
        help="build a semi-standalone bundle.",
    )
    parser.add_argument(
        "--alias",
        "-A",
        dest="build_type",
        default=_config.BuildType.SEMI_STANDALONE,
        action="store_const",
        const=_config.BuildType.ALIAS,
        help="build an alias bundle.",
    )

    # XXX, consider  making this multi-value
    #      (but: at the moment there is no verbosity
    #       in the first place)
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="print more information while building.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args(argv)

    try:
        with open(args.pyproject, "rb") as stream:
            contents = tomllib.load(stream)
    except OSError as exc:
        print(f"Cannot open {str(args.pyproject)!r}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        config = _config.parse_pyproject(contents, args.pyproject.parent)
    except _config.ConfigurationError as exc:
        print(f"{args.pyproject}: {exc}", file=sys.stderr)
        sys.exit(1)

    # XXX: I don't particularly like poking directly in '_locals'
    if args.build_type is not None:
        config._local["build-type"] = args.build_type
    return args.verbose, config


def main():
    verbose, config = parse_arguments(sys.argv[1:])

    progress = _progress.Progress(level=2 if verbose else 1)
    task_id = progress.add_task("Processing bundles", len(config.bundles))

    ok = True
    for bundle in config.bundles:
        # XXX: Sort bundles to ensure nested bundles get build
        #      after their enclosing bundle.
        progress.update(
            task_id,
            current=f"{bundle.build_type.value} {'plugin' if bundle.plugin else 'application'} {bundle.name!r}",
        )
        _builder.build_bundle(config, bundle, progress) and ok
        progress.step_task(task_id)
    progress.update(task_id, current="")
    progress._progress.stop()

    # XXX: Report on the results
    sys.exit(1 if progress.have_error else 0)


if __name__ == "__main__":
    main()
