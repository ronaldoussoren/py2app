import ast
import contextlib
import errno
import importlib.metadata
import os
import stat
import subprocess
import sys
import time
import typing

import macholib.util
from macholib.util import is_platform_file
from modulegraph import zipio
from modulegraph.find_modules import PY_SUFFIXES

gConverterTab = {}


def find_converter(source):
    if not gConverterTab:
        for ep in importlib.metadata.entry_points(group="py2app.converter"):
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


def copy_resource(source, destination, dry_run=0, symlink=0):
    """
    Copy a resource file into the application bundle
    """
    if hasattr(source, "getvalue"):
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
        for fn in zipio.listdir(source):
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
    source,
    destination,
    preserve_mode=False,
    preserve_times=False,
    update=False,
    dry_run=0,
    progress=None,
):
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
                    "copying file %s failed due to spurious EAGAIN, "
                    "retrying in 2 seconds",
                    source,
                )
            time.sleep(2)


def _copy_file(
    source,
    destination,
    preserve_mode=False,
    preserve_times=False,
    update=False,
    dry_run=0,
    progress=None,
):
    if progress is not None:
        progress.trace(f"copying file {source} -> {destination}")
    with zipio.open(source, "rb") as fp_in:
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
                    mode = zipio.getmode(source)

                elif os.path.isfile(source):
                    mode = stat.S_IMODE(os.stat(source).st_mode)

                if mode is not None:
                    os.chmod(destination, mode)

            if preserve_times:
                mtime = zipio.getmtime(source)
                os.utime(destination, (mtime, mtime))


def make_symlink(source, target):
    if os.path.islink(target):
        os.unlink(target)

    os.symlink(source, target)


def newer(source, target):
    """
    distutils.dep_utils.newer with zipfile support
    """
    try:
        return zipio.getmtime(source) > zipio.getmtime(target)
    except OSError:
        return True


def find_version(fn: os.PathLike) -> typing.Optional[str]:
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


def in_system_path(filename):
    """
    Return True if the file is in a system path
    """
    return macholib.util.in_system_path(filename)


def make_exec(path):
    mask = os.umask(0)
    os.umask(mask)
    os.chmod(path, os.stat(path).st_mode | (0o111 & ~mask))


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


def mergecopy(src, dest):
    return macholib.util.mergecopy(src, dest)


def mergetree(src, dst, condition=None, copyfn=mergecopy):
    """Recursively merge a directory tree using mergecopy()."""
    return macholib.util.mergetree(src, dst, condition=condition, copyfn=copyfn)


def move(src, dst):
    return macholib.util.move(src, dst)


def copy2(src, dst):
    return macholib.util.copy2(src, dst)


def fancy_split(s, sep=","):
    # a split which also strips whitespace from the items
    # passing a list or tuple will return it unchanged
    if s is None:
        return []
    if hasattr(s, "split"):
        return [item.strip() for item in s.split(sep)]
    return s


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


def make_loader(fn):
    return LOADER % fn


def byte_compile(
    py_files,
    optimize=0,
    force=0,
    target_dir=None,
    progress=None,
    dry_run=0,
    direct=None,
):

    if direct is None:
        direct = __debug__ and optimize == 0

    # "Indirect" byte-compilation: write a temporary script and then
    # run it with the appropriate flags.
    if not direct:
        # XXX: This needs work to play nice with rich.progress
        from distutils.util import execute, spawn
        from tempfile import NamedTemporaryFile

        progress.info("writing byte-compilation script")
        if not dry_run:
            with NamedTemporaryFile(
                suffix=".py", delete=False, mode="w", encoding="utf-8"
            ) as script:
                script_name = script.name
                script.write(
                    """
from py2app.util import byte_compile
from modulegraph.modulegraph import *
files = [
"""
                )

                for f in py_files:
                    script.write(repr(f) + ",\n")
                script.write("]\n")
                script.write(
                    """
byte_compile(files, optimize=%r, force=%r,
             target_dir=%r,
             progress=None, dry_run=0,
             direct=1)
"""
                    % (optimize, force, target_dir)
                )

        # Ensure that py2app is on PYTHONPATH, this ensures that
        # py2app.util can be found even when we're running from
        # an .egg that was downloaded by setuptools
        import py2app

        pp = os.path.dirname(os.path.dirname(py2app.__file__))
        if "PYTHONPATH" in os.environ:
            pp = "{}:{}".format(pp, os.environ["PYTHONPATH"])

        cmd = ["/usr/bin/env", f"PYTHONPATH={pp}", sys.executable, script_name]

        if optimize == 1:
            cmd.insert(3, "-O")
        elif optimize == 2:
            cmd.insert(3, "-OO")
        spawn(cmd, verbose=1, dry_run=dry_run)
        execute(
            os.remove,
            (script_name,),
            "removing %s" % script_name,
            verbose=1,
            dry_run=dry_run,
        )

    else:
        from py_compile import compile

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

                        compile(fn, cfile, dfile)
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
                    progress.info(
                        f"skipping byte-compilation of {mod.filename} to {dfile}"
                    )

            if progress is not None:
                progress.step_task(task_id)

        if progress is not None:
            progress._progress.stop_task(task_id)


SCMDIRS = ["CVS", ".svn", ".hg", ".git"]


def skipscm(ofn):
    fn = os.path.basename(ofn)
    if fn in SCMDIRS:
        return False
    return True


def skipfunc(junk=(), junk_exts=(), chain=()):
    junk = set(junk)
    junk_exts = set(junk_exts)
    chain = tuple(chain)

    def _skipfunc(fn):
        if os.path.basename(fn) in junk:
            return False
        elif os.path.splitext(fn)[1] in junk_exts:
            return False
        for func in chain:
            if not func(fn):
                return False
        else:
            return True

    return _skipfunc


JUNK = [".DS_Store", ".gdb_history", "build", "dist"] + SCMDIRS
JUNK_EXTS = [".pbxuser", ".pyc", ".pyo", ".swp"]
skipjunk = skipfunc(JUNK, JUNK_EXTS)


def iter_platform_files(path, is_platform_file=macholib.util.is_platform_file):
    """
    Iterate over all of the platform files in a directory
    """
    for root, _dirs, files in os.walk(path):
        for fn in files:
            fn = os.path.join(root, fn)
            if is_platform_file(fn):
                yield fn


def strip_files(files, dry_run=0, progress=None):
    """
    Strip the given set of files
    """
    if dry_run:
        return

    # XXX: macholib.util.strip_files just calls strip(1)
    # return macholib.util.strip_files(files)

    task_id = progress.add_task("Stripping binaries", len(files))
    for name in files:
        progress.trace(f"Stripping {name}")
        with reset_blocking_status():
            subprocess.check_call(
                ["/usr/bin/strip", "-x", "-S", "-", name], stderr=subprocess.DEVNULL
            )
        progress.step_task(task_id)

    progress._progress.stop_task(task_id)


def copy_tree(
    src,
    dst,
    preserve_mode=1,
    preserve_times=1,
    preserve_symlinks=0,
    update=0,
    verbose=0,
    dry_run=0,
    condition=None,
    progress=None,
):

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

    from distutils.dep_util import newer
    from distutils.errors import DistutilsFileError

    if condition is None:
        condition = skipscm

    if not dry_run and not zipio.isdir(src):
        raise DistutilsFileError("cannot copy tree '%s': not a directory" % src)
    try:
        names = zipio.listdir(src)
    except os.error as exc:
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
                if update and not newer(src, dst_name):
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
                preserve_mode,
                preserve_times,
                update,
                dry_run=dry_run,
                progress=progress,
            )
            outputs.append(dst_name)

    return outputs


def walk_files(path):
    for _root, _dirs, files in os.walk(path):
        yield from files


def find_app(app):
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


_tools = {}


def _get_tool(toolname):
    if toolname not in _tools:
        if os.path.exists("/usr/bin/xcrun"):
            try:
                _tools[toolname] = subprocess.check_output(
                    ["/usr/bin/xcrun", "-find", toolname]
                )[:-1]
            except subprocess.CalledProcessError:
                raise OSError(f"Tool {toolname!r} not found")

        else:
            # Support for Xcode 3.x and earlier
            if toolname == "momc":
                choices = [
                    (
                        "/Library/Application Support/Apple/"
                        "Developer Tools/Plug-ins/XDCoreDataModel.xdplugin/"
                        "Contents/Resources/momc"
                    ),
                    (
                        "/Developer/Library/Xcode/Plug-ins/"
                        "XDCoreDataModel.xdplugin/Contents/Resources/momc"
                    ),
                    "/Developer/usr/bin/momc",
                ]
            elif toolname == "mapc":
                choices = [
                    (
                        "/Developer/Library/Xcode/Plug-ins/"
                        "XDMappingModel.xdplugin/"
                        "Contents/Resources/mapc",
                    ),
                    "/Developer/usr/bin/mapc",
                ]
            else:
                raise OSError(f"Tool {toolname!r} not found")

            for fn in choices:
                if os.path.exists(fn):
                    _tools[toolname] = fn
                    break
            else:
                raise OSError(f"Tool {toolname!r} not found")
    return _tools[toolname]


def momc(src, dst):
    with reset_blocking_status():
        subprocess.check_call([_get_tool("momc"), src, dst])


def mapc(src, dst):
    with reset_blocking_status():
        subprocess.check_call([_get_tool("mapc"), src, dst])


def _macho_find(path):
    for basename, _dirs, files in os.walk(path):
        for fn in files:
            path = os.path.join(basename, fn)
            if is_platform_file(path):
                yield path


def _dosign(*path, progress=None):
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
            progress.warning(f"{path}: {out}")
            raise subprocess.CalledProcessError(xit, "codesign")


def codesign_adhoc(bundle, progress):
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
def reset_blocking_status():
    """
    Contextmanager that resets the non-blocking status of
    the std* streams as necessary. Used with all calls of
    xcode tools, mostly because ibtool tends to set the
    std* streams to non-blocking.
    """
    import fcntl
    import os

    blocking = [fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_NONBLOCK for fd in (0, 1, 2)]

    try:
        yield

    finally:
        for fd, is_blocking in zip((0, 1, 2), blocking):
            cur = fcntl.fcntl(fd, fcntl.F_GETFL)
            if is_blocking:
                reset = cur & ~os.O_NONBLOCK
            else:
                reset = cur | os.O_NONBLOCK

            if cur != reset:
                print(f"Resetting blocking status of {fd}")
                fcntl.fcntl(fd, fcntl.F_SETFL, reset)
