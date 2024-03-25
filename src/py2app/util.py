import ast
import collections.abc
import contextlib
import errno
import fcntl
import io
import os
import pathlib
import stat
import subprocess
import sys
import time
import typing
from py_compile import compile

import macholib.util
from macholib.util import is_platform_file
from modulegraph import zipio
from modulegraph.find_modules import PY_SUFFIXES
from modulegraph.modulegraph import Node

from .progress import Progress

if sys.version_info[:2] < (3, 10):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

gConverterTab: typing.Dict[str, typing.Callable[..., None]] = {}  # XXX


def find_converter(
    source: typing.Union[str, os.PathLike[str]]
) -> typing.Optional[typing.Callable[..., None]]:
    if not gConverterTab:
        for ep in importlib_metadata.entry_points(group="py2app.converter"):
            if sys.version_info[:2] >= (3, 10):
                assert isinstance(
                    ep, importlib_metadata.EntryPoint
                ), f"{ep!r} is not an EntryPoint but {type(ep)!r}"
            function = ep.load()
            if hasattr(function, "py2app_suffix"):
                print(f"WARNING: using 'py2app_suffix' is deprecated for {function}")
                suffix = function.py2app_suffix
            else:
                suffix = f".{ep.name}"
            gConverterTab[suffix] = function

    basename, suffix = os.path.splitext(source)
    try:
        return gConverterTab[suffix]

    except KeyError:
        return None


def copy_resource(
    source: typing.Union[io.StringIO, os.PathLike[str], str],
    destination: typing.Union[os.PathLike[str], str],
    dry_run: bool = False,
    symlink: bool = False,
) -> None:
    """
    Copy a resource file into the application bundle
    """
    if isinstance(source, io.StringIO):
        if not dry_run:
            contents = source.getvalue()

            if isinstance(contents, bytes):
                mode = "wb"
            else:
                mode = "w"

            if os.path.exists(destination):
                os.unlink(destination)
            with open(destination, mode) as fp:
                fp.write(contents)
        return

    converter = find_converter(source)
    if converter is not None:
        converter(source, destination, dry_run=dry_run)
        return

    if os.path.isdir(source):
        if not dry_run:
            if not os.path.exists(destination):
                os.mkdir(destination)
        for fn in zipio.listdir(os.fspath(source)):
            copy_resource(
                os.path.join(source, fn),
                os.path.join(destination, fn),
                dry_run=dry_run,
                symlink=symlink,
            )

    else:
        if symlink:
            if not dry_run:
                make_symlink(os.path.abspath(source), destination)

        else:
            copy_file(source, destination, dry_run=dry_run, preserve_mode=True)


def copy_file(
    source: typing.Union[os.PathLike[str], str],
    destination: typing.Union[os.PathLike[str], str],
    preserve_mode: bool = False,
    preserve_times: bool = False,
    update: bool = False,
    dry_run: bool = False,
    progress: typing.Optional[Progress] = None,
) -> None:
    while True:
        try:
            _copy_file(
                source,
                destination,
                preserve_mode,
                preserve_times,
                update,
                dry_run,
                progress,
            )
            return
        except OSError as exc:
            if exc.errno != errno.EAGAIN:
                raise

            if progress is not None:
                progress.warning(
                    f"copying file {source} failed due to spurious EAGAIN, "
                    "retrying in 2 seconds",
                )
            time.sleep(2)


def _copy_file(
    source: typing.Union[os.PathLike[str], str],
    destination: typing.Union[os.PathLike[str], str],
    preserve_mode: bool = False,
    preserve_times: bool = False,
    update: bool = False,
    dry_run: bool = False,
    progress: typing.Optional[Progress] = None,
) -> None:
    if progress is not None:
        progress.trace(f"copying file {source} -> {destination}")
    with zipio.open(os.fspath(source), "rb") as fp_in:
        if not dry_run:
            if os.path.isdir(destination):
                destination = os.path.join(destination, os.path.basename(source))
            if os.path.exists(destination):
                os.unlink(destination)

            with open(destination, "wb") as fp_out:
                data = fp_in.read()
                fp_out.write(data)

            if preserve_mode:
                mode = None
                if hasattr(zipio, "getmode"):
                    mode = zipio.getmode(os.fspath(source))

                elif os.path.isfile(source):
                    mode = stat.S_IMODE(os.stat(source).st_mode)

                if mode is not None:
                    os.chmod(destination, mode)

            if preserve_times:
                mtime = zipio.getmtime(os.fspath(source))
                os.utime(destination, (mtime, mtime))


def make_symlink(
    source: typing.Union[os.PathLike[str], str],
    target: typing.Union[os.PathLike[str], str],
) -> None:
    if os.path.islink(target):
        os.unlink(target)

    os.symlink(source, target)


def newer(
    source: typing.Union[os.PathLike[str], str],
    target: typing.Union[os.PathLike[str], str],
) -> bool:
    """
    distutils.dep_utils.newer with zipfile support
    """
    try:
        return zipio.getmtime(os.fspath(source)) > zipio.getmtime(os.fspath(target))
    except OSError:
        return True


def find_version(fn: typing.Union[str, os.PathLike]) -> typing.Optional[str]:
    """
    Try to find a toplevel statement assigning a constant
    to ``__version__`` and return the value. When multiple
    assignments are found, use the last one.

    Returns None when no valid ``__version__`` is found.
    """
    with open(fn, "rb") as stream:
        # Read source in binary mode, reading in text mode
        # would require handling encoding tokens.
        source = stream.read()

    module_ast = ast.parse(source, str(fn))

    # Look for a toplevel assignment statement that sets
    # __version__ to a constant value
    #
    # Don't look inside conditional statement because there's
    # no good way to assess which branch should be used.
    #
    result = None
    for node in module_ast.body:
        if not isinstance(node, ast.Assign):
            continue

        for t in node.targets:
            if not isinstance(t, ast.Name):
                continue
            if t.id == "__version__":
                value = node.value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    result = value.value
                else:
                    result = None
    return result


def in_system_path(filename: typing.Union[os.PathLike[str], str]) -> bool:
    """
    Return True if the file is in a system path
    """
    return macholib.util.in_system_path(os.fspath(filename))


def make_exec(path: typing.Union[os.PathLike[str], str]) -> None:
    mask = os.umask(0)
    os.umask(mask)
    os.chmod(path, os.stat(path).st_mode | (0o111 & ~mask))


def makedirs(path: typing.Union[os.PathLike[str], str]) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def mergecopy(
    src: typing.Union[os.PathLike[str], str], dest: typing.Union[os.PathLike[str], str]
) -> None:
    macholib.util.mergecopy(os.fspath(src), os.fspath(dest))


def mergetree(
    src: typing.Union[os.PathLike[str], str],
    dst: typing.Union[os.PathLike[str], str],
    condition: typing.Optional[typing.Callable[[str], bool]] = None,
    copyfn: typing.Callable[[str, str], None] = mergecopy,
) -> None:
    """Recursively merge a directory tree using mergecopy()."""
    macholib.util.mergetree(
        os.fspath(src), os.fspath(dst), condition=condition, copyfn=copyfn
    )


def move(
    src: typing.Union[os.PathLike[str], str], dst: typing.Union[os.PathLike[str], str]
) -> None:
    macholib.util.move(os.fspath(src), os.fspath(dst))


def copy2(
    src: typing.Union[os.PathLike[str], str], dst: typing.Union[os.PathLike[str], str]
) -> None:
    macholib.util.copy2(os.fspath(src), os.fspath(dst))


def fancy_split(s: typing.Any, sep: str = ",") -> typing.List[str]:
    # a split which also strips whitespace from the items
    # passing a list or tuple will return it unchanged
    # This accepts "Any" because the value is passed through setup.py
    if s is None:
        return []
    elif isinstance(s, str):
        return [item.strip() for item in s.split(sep)]
    elif isinstance(s, collections.abc.Sequence):
        result: typing.List[str] = []
        for item in s:
            if isinstance(item, str):
                result.append(item)
            else:
                raise RuntimeError(f"{item!r} is not a string")

        return result
    else:
        raise RuntimeError("Invalid type for {s!r}")


LOADER = """
def __load():
    import imp, os, sys
    ext = %r
    for path in sys.path:
        if not path.endswith('lib-dynload'):
            continue
        ext_path = os.path.join(path, ext)
        if os.path.exists(ext_path):
            mod = imp.load_dynamic(__name__, ext_path)
            break
    else:
        raise ImportError(repr(ext) + " not found")
__load()
del __load
"""


def make_loader(fn: str) -> str:
    return LOADER % fn


def byte_compile(
    py_files: typing.Sequence[Node],
    force: bool = False,
    target_dir: typing.Optional[typing.Union[os.PathLike[str], str]] = None,
    progress: typing.Optional[Progress] = None,
    dry_run: bool = False,
    optimize: int = -1,
) -> None:
    if progress is not None:
        task_id = progress.add_task("Byte compiling", len(py_files))
    for mod in py_files:
        # Terminology from the py_compile module:
        #   cfile - byte-compiled file
        #   dfile - purported source filename (same as 'file' by default)
        if mod.filename == mod.identifier:
            cfile = os.path.basename(mod.filename)
            dfile = cfile + (__debug__ and "c" or "o")
        else:
            cfile = mod.identifier.replace(".", os.sep)

            if mod.packagepath:
                dfile = cfile + os.sep + "__init__.pyc"
            else:
                dfile = cfile + ".pyc"
        if target_dir:
            cfile = os.path.join(target_dir, dfile)

        assert mod.filename is not None
        if force or newer(mod.filename, cfile):
            if progress is not None:
                progress.trace(f"byte-compiling {mod.filename} to {dfile}")

            if not dry_run:
                if not os.path.exists(os.path.dirname(cfile)):
                    if progress is not None:
                        progress.trace(f"create {os.path.dirname(cfile)}")
                    os.makedirs(os.path.dirname(cfile), 0o777)
                suffix = os.path.splitext(mod.filename)[1]

                if suffix in (".py", ".pyw"):
                    fn = cfile + ".py"

                    with zipio.open(mod.filename, "rb") as fp_in:
                        with open(fn, "wb") as fp_out:
                            fp_out.write(fp_in.read())

                    compile(fn, cfile, dfile, optimize=optimize)
                    os.unlink(fn)

                elif suffix in PY_SUFFIXES:
                    # Minor problem: This will happily copy a file
                    # <mod>.pyo to <mod>.pyc or <mod>.pyc to
                    # <mod>.pyo, but it does seem to work.
                    copy_file(mod.filename, cfile, preserve_times=True)

                else:
                    raise RuntimeError("Don't know how to handle %r" % mod.filename)
        else:
            if progress is not None:
                progress.info(f"skipping byte-compilation of {mod.filename} to {dfile}")

        if progress is not None:
            progress.step_task(task_id)

    if progress is not None:
        progress._progress.stop_task(task_id)


SCMDIRS = ["CVS", ".svn", ".hg", ".git"]


def skipscm(ofn: typing.Union[os.PathLike[str], str]) -> bool:
    fn = os.path.basename(ofn)
    if fn in SCMDIRS:
        return False
    return True


def skipfunc(
    junk: typing.Sequence[str] = (),
    junk_exts: typing.Sequence[str] = (),
    chain: typing.Sequence[
        typing.Callable[[typing.Union[os.PathLike[str], str]], bool]
    ] = (),
) -> typing.Callable[[typing.Union[os.PathLike[str], str]], bool]:
    junk_set = set(junk)
    junk_exts_set = set(junk_exts)
    chain_funcs = tuple(chain)

    def _skipfunc(fn: typing.Union[os.PathLike[str], str]) -> bool:
        if os.path.basename(fn) in junk_set:
            return False
        elif os.path.splitext(fn)[1] in junk_exts_set:
            return False
        for func in chain_funcs:
            if not func(fn):
                return False
        else:
            return True

    return _skipfunc


JUNK = [".DS_Store", ".gdb_history", "build", "dist"] + SCMDIRS
JUNK_EXTS = [".pbxuser", ".pyc", ".pyo", ".swp"]
skipjunk = skipfunc(JUNK, JUNK_EXTS)


def iter_platform_files(
    path: typing.Union[os.PathLike[str], str],
    is_platform_file: typing.Callable[[str], bool] = macholib.util.is_platform_file,
) -> typing.Iterator[str]:
    """
    Iterate over all of the platform files in a directory
    """
    for root, _dirs, files in os.walk(path):
        for fn in files:
            fn = os.path.join(root, fn)
            if is_platform_file(fn):
                yield fn


# XXX: Progress argument should not be optional
def strip_files(
    files: typing.Sequence[typing.Union[os.PathLike[str], str]],
    dry_run: bool = False,
    progress: typing.Optional[Progress] = None,
) -> None:
    """
    Strip the given set of files
    """
    if dry_run:
        return

    # XXX: macholib.util.strip_files just calls strip(1)
    # return macholib.util.strip_files(files)

    if progress is not None:
        task_id = progress.add_task("Stripping binaries", len(files))
    for name in files:
        if progress is not None:
            progress.trace(f"Stripping {name}")
        with reset_blocking_status():
            subprocess.check_call(
                ["/usr/bin/strip", "-x", "-S", "-", name], stderr=subprocess.DEVNULL
            )
        if progress is not None:
            progress.step_task(task_id)

    if progress is not None:
        progress._progress.stop_task(task_id)


def copy_tree(
    src: str,
    dst: str,
    preserve_mode: int = 1,
    preserve_times: int = 1,
    preserve_symlinks: int = 0,
    update: bool = False,
    verbose: int = 0,
    dry_run: bool = False,
    condition: typing.Optional[typing.Callable[[str], bool]] = None,
    progress: typing.Optional[Progress] = None,
) -> typing.List[str]:
    """
    Copy an entire directory tree 'src' to a new location 'dst'.  Both
    'src' and 'dst' must be directory names.  If 'src' is not a
    directory, raise DistutilsFileError.  If 'dst' does not exist, it is
    created with 'mkpath()'.  The end result of the copy is that every
    file in 'src' is copied to 'dst', and directories under 'src' are
    recursively copied to 'dst'.  Return the list of files that were
    copied or might have been copied, using their output name.  The
    return value is unaffected by 'update' or 'dry_run': it is simply
    the list of all files under 'src', with the names changed to be
    under 'dst'.

    'preserve_mode' and 'preserve_times' are the same as for
    'copy_file'; note that they only apply to regular files, not to
    directories.  If 'preserve_symlinks' is true, symlinks will be
    copied as symlinks (on platforms that support them!); otherwise
    (the default), the destination of the symlink will be copied.
    'update' and 'verbose' are the same as for 'copy_file'.
    """
    assert isinstance(src, str), repr(src)
    assert isinstance(dst, str), repr(dst)

    from distutils.dep_util import newer as distutils_newer
    from distutils.errors import DistutilsFileError

    if condition is None:
        condition = skipscm

    if not dry_run and not zipio.isdir(src):
        raise DistutilsFileError("cannot copy tree '%s': not a directory" % src)
    try:
        names = zipio.listdir(src)
    except OSError as exc:
        (errno, errstr) = exc.args
        if dry_run:
            names = []
        else:
            raise DistutilsFileError(f"error listing files in '{src}': {errstr}")

    if not dry_run and not os.path.exists(dst):
        if progress is not None:
            progress.trace(f"creating {dst}")
        os.makedirs(dst, 0o777)

    outputs = []

    for n in names:
        src_name = os.path.join(src, n)
        dst_name = os.path.join(dst, n)
        if (condition is not None) and (not condition(src_name)):
            continue

        # Note: using zipio's internal _locate function throws an IOError on
        # dead symlinks, so handle it here.
        if os.path.islink(src_name) and not os.path.exists(
            os.path.join(src, os.readlink(src_name))
        ):
            continue

        if preserve_symlinks and zipio.islink(src_name):
            link_dest = zipio.readlink(src_name)
            if progress is not None:
                progress.trace(f"linking {dst_name} -> {link_dest}")
            if not dry_run:
                if update and not distutils_newer(src, dst_name):
                    pass
                else:
                    make_symlink(link_dest, dst_name)
            outputs.append(dst_name)

        elif zipio.isdir(src_name) and not os.path.isfile(src_name):
            # ^^^ this odd tests ensures that resource files that
            # happen to be a zipfile won't get extracted.
            outputs.extend(
                copy_tree(
                    src_name,
                    dst_name,
                    preserve_mode,
                    preserve_times,
                    preserve_symlinks,
                    update,
                    dry_run=dry_run,
                    condition=condition,
                    progress=progress,
                )
            )
        else:
            copy_file(
                src_name,
                dst_name,
                bool(preserve_mode),
                bool(preserve_times),
                update,
                dry_run=dry_run,
                progress=progress,
            )
            outputs.append(dst_name)

    return outputs


def walk_files(path: typing.Union[os.PathLike[str], str]) -> typing.Iterator[str]:
    for _root, _dirs, files in os.walk(path):
        yield from files


def find_app(app: typing.Union[os.PathLike[str], str]) -> typing.Optional[str]:
    dpath = os.path.realpath(app)
    if os.path.exists(dpath):
        return dpath
    if os.path.isabs(app):
        return None
    for path in os.environ.get("PATH", "").split(":"):
        dpath = os.path.realpath(os.path.join(path, app))
        if os.path.exists(dpath):
            return dpath
    return None


_tools: typing.Dict[str, str] = {}


def get_tool(toolname: str) -> str:
    if toolname not in _tools:
        try:
            _tools[toolname] = (
                subprocess.check_output(["/usr/bin/xcrun", "-find", toolname])
                .decode()
                .strip()
            )
        except subprocess.CalledProcessError:
            raise OSError(f"Tool {toolname!r} not found")

    return _tools[toolname]


def momc(
    src: typing.Union[os.PathLike[str], str], dst: typing.Union[os.PathLike[str], str]
) -> None:
    with reset_blocking_status():
        subprocess.check_call([get_tool("momc"), os.fspath(src), os.fspath(dst)])


def mapc(
    src: typing.Union[os.PathLike[str], str], dst: typing.Union[os.PathLike[str], str]
) -> None:
    with reset_blocking_status():
        subprocess.check_call([get_tool("mapc"), os.fspath(src), os.fspath(dst)])


def _macho_find(path: typing.Union[os.PathLike[str], str]) -> typing.Iterator[str]:
    for basename, _dirs, files in os.walk(path):
        for fn in files:
            path = os.path.join(basename, fn)
            if is_platform_file(path):
                yield path


def _dosign(
    *path: typing.Union[os.PathLike[str], str],
    progress: typing.Optional[Progress] = None,
) -> None:
    with reset_blocking_status():
        p = subprocess.Popen(
            (
                "codesign",
                "-s",
                "-",
                "--preserve-metadata=identifier,entitlements,flags,runtime",
                "-f",
            )
            + path,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
        )

        out, _ = p.communicate()
        xit = p.wait()
        if xit != 0:
            if progress is not None:
                progress.warning(f"{path}: {out.decode()}")
            raise subprocess.CalledProcessError(xit, "codesign")


def codesign_adhoc(
    bundle: typing.Union[os.PathLike[str], str], progress: Progress
) -> None:
    """
    (Re)sign a bundle

    Signing should be done "depth-first", sign
    libraries before signing the libraries/executables
    linking to them.

    The current implementation is a crude hack,
    but is better than nothing. Signing properly requires
    performing a topological sort using dependencies.

    "codesign" will resign the entire bundle, but only
    if partial signatures are valid.
    """
    # try:
    #    _dosign(bundle)
    #    return
    # except subprocess.CalledProcessError:
    #    pass

    platfiles = list(_macho_find(bundle))

    task_id = progress.add_task("Signing code", len(platfiles) + 1)
    while platfiles:
        for file in platfiles:
            failed = []
            try:
                progress.trace(f"Signing {file}")
                _dosign(file, progress=progress)
                progress.step_task(task_id)
            except subprocess.CalledProcessError:
                progress.info(f"Signing {file} failed")
                failed.append(file)
        if failed == platfiles:
            raise RuntimeError(f"Cannot sign bundle {bundle!r}")
        platfiles = failed

    for _ in range(5):
        try:
            progress.info(f"Signing {bundle}")
            _dosign(bundle, progress=progress)
            break
        except subprocess.CalledProcessError:
            progress.warning(f"Signing {bundle} failed")
            time.sleep(1)
            continue
    progress.step_task(task_id)
    progress._progress.stop_task(task_id)


@contextlib.contextmanager
def reset_blocking_status() -> typing.Iterator[None]:
    """
    Contextmanager that resets the non-blocking status of
    the std* streams as necessary. Used with all calls of
    xcode tools, mostly because ibtool tends to set the
    std* streams to non-blocking.
    """
    orig_nonblocking = [
        fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_NONBLOCK for fd in (0, 1, 2)
    ]

    try:
        yield

    finally:
        for fd, is_nonblocking in zip((0, 1, 2), orig_nonblocking):
            cur = fcntl.fcntl(fd, fcntl.F_GETFL)
            if is_nonblocking:
                reset = cur | os.O_NONBLOCK
            else:
                reset = cur & ~os.O_NONBLOCK

            if cur != reset:
                print(
                    f"Resetting blocking status of {fd} to"
                    f" {'non-blocking' if is_nonblocking else 'blocking'}"
                )
                fcntl.fcntl(fd, fcntl.F_SETFL, reset)


def make_path(value: typing.Union[str, os.PathLike[str]]) -> pathlib.Path:
    if isinstance(value, pathlib.Path):
        return value

    return pathlib.Path(value)
