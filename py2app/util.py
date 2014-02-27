from __future__ import print_function

import os, sys, imp, time, errno, stat
from modulegraph.find_modules import PY_SUFFIXES, C_SUFFIXES
from modulegraph.util import *
from modulegraph import zipio
import macholib.util
import warnings
from distutils import log

import pkg_resources
import subprocess

# Deprecated functionality
def os_path_islink(path):
    warnings.warn("Use zipio.islink instead of os_path_islink",
            DeprecationWarning)
    return zipio.islink(path)

def os_path_isdir(path):
    warnings.warn("Use zipio.isdir instead of os_path_isdir",
            DeprecationWarning)
    return zipio.islink(path)

def os_readlink(path):
    warnings.warn("Use zipio.readlink instead of os_readlink",
            DeprecationWarning)
    return zipio.islink(path)

import zipfile
def get_zip_data(path_to_zip, path_in_zip):
    warnings.warn("Use zipio.open instead of get_zip_data",
            DeprecationWarning)
    zf = zipfile.ZipFile(path_to_zip)
    return zf.read(path_in_zip)

def path_to_zip(path):
    """
    Returns (pathtozip, pathinzip). If path isn't in a zipfile pathtozip
    will be None
    """
    warnings.warn("Don't use this function", DeprecationWarning)
    zf = zipfile.ZipFile(path_to_zip)
    orig_path = path
    from distutils.errors import DistutilsFileError
    if os.path.exists(path):
        return (None, path)

    else:
        rest = ''
        while not os.path.exists(path):
            path, r = os.path.split(path)
            if not path:
                raise DistutilsFileError("File doesn't exist: %s"%(orig_path,))
            rest = os.path.join(r, rest)

        if not os.path.isfile(path):
            # Directory really doesn't exist
            raise DistutilsFileError("File doesn't exist: %s"%(orig_path,))

        try:
            zf = zipfile.ZipFile(path)
        except zipfile.BadZipfile:
            raise DistutilsFileError("File doesn't exist: %s"%(orig_path,))

        if rest.endswith('/'):
            rest = rest[:-1]

        return path, rest

def get_mtime(path, mustExist=True):
    """
    Get mtime of a path, even if it is inside a zipfile
    """
    warnings.warn("Don't use this function", DeprecationWarning)
    try:
        return zipio.getmtime(target)

    except IOError:
        if not mustExist:
            return -1

        raise

# End deprecated functionality

gConverterTab = {}
def find_converter(source):
    if not gConverterTab:
        for ep in pkg_resources.iter_entry_points('py2app.converter'):
            function = ep.load()
            if not hasattr(function, "py2app_suffix"):
                print("WARNING: %s does not have 'py2app_suffix' attribute"%(function))
                continue
            gConverterTab[function.py2app_suffix] = function

    basename, suffix = os.path.splitext(source)
    try:
        return gConverterTab[suffix]

    except KeyError:
        return None

def copy_resource(source, destination, dry_run=0, symlink=0):
    """
    Copy a resource file into the application bundle
    """
    import py2app.converters as conv

    converter = find_converter(source)
    if converter is not None:
        converter(source, destination, dry_run=dry_run)
        return

    if os.path.isdir(source):
        if not dry_run:
            if not os.path.exists(destination):
                os.mkdir(destination)
        for fn in zipio.listdir(source):
            copy_resource(os.path.join(source, fn),
                    os.path.join(destination, fn), dry_run=dry_run, symlink=symlink)

    else:
        if symlink:
            if not dry_run:
                if os.path.exists(destination):
                    os.unlink(destination)
                os.symlink(os.path.abspath(source), destination)

        else:
            copy_file(source, destination, dry_run=dry_run, preserve_mode=True)



def copy_file(source, destination, preserve_mode=False, preserve_times=False, update=False, dry_run=0):
    while True:
        try:
            _copy_file(source, destination, preserve_mode, preserve_times, update, dry_run)
            return
        except IOError as exc:
            if exc.errno != errno.EAGAIN:
                raise

            log.info("copying file %s failed due to spurious EAGAIN, retrying in 2 seconds", source)
            time.sleep(2)

def _copy_file(source, destination, preserve_mode=False, preserve_times=False, update=False, dry_run=0):
    log.info("copying file %s -> %s", source, destination)
    with zipio.open(source, 'rb') as fp_in:
        if not dry_run:
            if os.path.exists(destination):
                os.unlink(destination)

            with open(destination, 'wb') as fp_out:
                data = fp_in.read()
                fp_out.write(data)

            if preserve_mode:
                mode = None
                if hasattr(zipio, 'getmode'):
                    mode = zipio.getmode(source)

                elif os.path.isfile(source):
                    mode = os.stat(source).st_mode

                if mode is not None:
                    os.chmod(destination, mode)

            if preserve_times:
                mtime = zipio.getmtime(source)
                os.utime(destination, (mtime, mtime))


def newer(source, target):
    """
    distutils.dep_utils.newer with zipfile support
    """
    try:
        return zipio.getmtime(source) > zipio.getmtime(target)
    except IOError:
        return True


def find_version(fn):
    """
    Try to find a __version__ assignment in a source file
    """
    return "0.0.0"
    import compiler
    from compiler.ast import Module, Stmt, Assign, AssName, Const
    ast = compiler.parseFile(fn)
    if not isinstance(ast, Module):
        raise ValueError("expecting Module")
    statements = ast.getChildNodes()
    if not (len(statements) == 1 and isinstance(statements[0], Stmt)):
        raise ValueError("expecting one Stmt")
    for node in statements[0].getChildNodes():
        if not isinstance(node, Assign):
            continue
        if not len(node.nodes) == 1:
            continue
        assName = node.nodes[0]
        if not (
                isinstance(assName, AssName) and
                isinstance(node.expr, Const) and
                assName.flags == 'OP_ASSIGN' and
                assName.name == '__version__'
                ):
            continue
        return node.expr.value
    else:
        raise ValueError("Version not found")

def in_system_path(filename):
    """
    Return True if the file is in a system path
    """
    return macholib.util.in_system_path(filename)

if sys.version_info[0] == 2:
    def fsencoding(s, encoding=sys.getfilesystemencoding()):
        return macholib.util.fsencoding(s, encoding=encoding)
else:
    def fsencoding(s, encoding=sys.getfilesystemencoding()):
        return s

def make_exec(path):
    mask = os.umask(0)
    os.umask(mask)
    os.chmod(path, os.stat(path).st_mode | (0o111 & ~mask))

def makedirs(path):
    path = fsencoding(path)
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

class FileSet(object):
    # A case insensitive but case preserving set of files
    def __init__(self, iterable=None):
        self._dict = {}
        if iterable is not None:
            for arg in iterable:
                self.add(arg)

    def __repr__(self):
        return "<FileSet %s at %x>" % (self._dict.values(), id(self))

    def add(self, fname):
        self._dict[fname.upper()] = fname

    def remove(self, fname):
        del self._dict[fname.upper()]

    def __contains__(self, fname):
        return fname.upper() in self._dict.keys()

    def __getitem__(self, index):
        key = self._dict.keys()[index]
        return self._dict[key]

    def __len__(self):
        return len(self._dict)

    def copy(self):
        res = FileSet()
        res._dict.update(self._dict)
        return res

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

def byte_compile(py_files, optimize=0, force=0,
                 target_dir=None, verbose=1, dry_run=0,
                 direct=None):

    if direct is None:
        direct = (__debug__ and optimize == 0)

    # "Indirect" byte-compilation: write a temporary script and then
    # run it with the appropriate flags.
    if not direct:
        from tempfile import mktemp
        from distutils.util import execute, spawn
        script_name = mktemp(".py")
        if verbose:
            print("writing byte-compilation script '%s'" % script_name)
        if not dry_run:
            with open(script_name, "w") as script:
                script.write("""
from py2app.util import byte_compile
from modulegraph.modulegraph import *
files = [
""")

                for f in py_files:
                    script.write(repr(f) + ",\n")
                script.write("]\n")
                script.write("""
byte_compile(files, optimize=%r, force=%r,
             target_dir=%r,
             verbose=%r, dry_run=0,
             direct=1)
""" % (optimize, force, target_dir, verbose))

        # Ensure that py2app is on PYTHONPATH, this ensures that
        # py2app.util can be found even when we're running from
        # an .egg that was downloaded by setuptools
        import py2app
        pp = os.path.dirname(os.path.dirname(py2app.__file__))
        if 'PYTHONPATH' in os.environ:
            pp = '%s:%s'%(pp, os.environ['PYTHONPATH'])

        cmd = ['/usr/bin/env', 'PYTHONPATH=%s'%(pp,), sys.executable, script_name]
        if optimize == 1:
            cmd.insert(3, "-O")
        elif optimize == 2:
            cmd.insert(3, "-OO")
        spawn(cmd, verbose=verbose, dry_run=dry_run)
        execute(os.remove, (script_name,), "removing %s" % script_name,
                verbose=verbose, dry_run=dry_run)


    else:
        from py_compile import compile
        from distutils.dir_util import mkpath

        for mod in py_files:
            # Terminology from the py_compile module:
            #   cfile - byte-compiled file
            #   dfile - purported source filename (same as 'file' by default)
            if mod.filename == mod.identifier:
                cfile = os.path.basename(mod.filename)
                dfile = cfile + (__debug__ and 'c' or 'o')
            else:
                cfile = mod.identifier.replace('.', os.sep)

                if mod.packagepath:
                    dfile = cfile + os.sep + '__init__.py' + (__debug__ and 'c' or 'o')
                else:
                    dfile = cfile + '.py' + (__debug__ and 'c' or 'o')
            if target_dir:
                cfile = os.path.join(target_dir, dfile)

            if force or newer(mod.filename, cfile):
                if verbose:
                    print("byte-compiling %s to %s" % (mod.filename, dfile))

                if not dry_run:
                    mkpath(os.path.dirname(cfile))
                    suffix = os.path.splitext(mod.filename)[1]

                    if suffix in ('.py', '.pyw'):
                        fn = cfile + '.py'

                        with zipio.open(mod.filename, 'rb') as fp_in:
                            with open(fn, 'wb') as fp_out:
                                fp_out.write(fp_in.read())

                        compile(fn, cfile, dfile)
                        os.unlink(fn)

                    elif suffix in PY_SUFFIXES:
                        # Minor problem: This will happily copy a file
                        # <mod>.pyo to <mod>.pyc or <mod>.pyc to
                        # <mod>.pyo, but it does seem to work.
                        copy_file(mod.filename, cfile, preserve_times=True)

                    else:
                        raise RuntimeError \
                              ("Don't know how to handle %r" % mod.filename)
            else:
                if verbose:
                    print("skipping byte-compilation of %s to %s" %
                          (mod.filename, dfile))

SCMDIRS = ['CVS', '.svn', '.hg', '.git']
def skipscm(ofn):
    ofn = fsencoding(ofn)
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

JUNK = ['.DS_Store', '.gdb_history', 'build', 'dist'] + SCMDIRS
JUNK_EXTS = ['.pbxuser', '.pyc', '.pyo', '.swp']
skipjunk = skipfunc(JUNK, JUNK_EXTS)

def get_magic(platform=sys.platform):
    if platform == 'darwin':
        import struct
        import macholib.mach_o
        return [
            struct.pack('!L', macholib.mach_o.MH_MAGIC),
            struct.pack('!L', macholib.mach_o.MH_CIGAM),
            struct.pack('!L', macholib.mach_o.MH_MAGIC_64),
            struct.pack('!L', macholib.mach_o.MH_CIGAM_64),
            struct.pack('!L', macholib.mach_o.FAT_MAGIC),
        ]
    elif platform == 'linux2':
        return ['\x7fELF']
    elif platform == 'win32':
        return ['MZ']
    return None

def iter_platform_files(path, is_platform_file=macholib.util.is_platform_file):
    """
    Iterate over all of the platform files in a directory
    """
    for root, dirs, files in os.walk(path):
        for fn in files:
            fn = os.path.join(root, fn)
            if is_platform_file(fn):
                yield fn

def strip_files(files, dry_run=0, verbose=0):
    """
    Strip the given set of files
    """
    if dry_run:
        return
    return macholib.util.strip_files(files)

def copy_tree(src, dst,
        preserve_mode=1,
        preserve_times=1,
        preserve_symlinks=0,
        update=0,
        verbose=0,
        dry_run=0,
        condition=None):

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
    assert isinstance(src, (str, unicode)), repr(src)
    assert isinstance(dst, (str, unicode)), repr(dst)


    from distutils.dir_util import mkpath
    from distutils.dep_util import newer
    from distutils.errors import DistutilsFileError
    from distutils import log

    src = fsencoding(src)
    dst = fsencoding(dst)

    if condition is None:
        condition = skipscm

    if not dry_run and not zipio.isdir(src):
        raise DistutilsFileError(
              "cannot copy tree '%s': not a directory" % src)
    try:
        names = zipio.listdir(src)
    except os.error as exc:
        (errno, errstr) = exc.args
        if dry_run:
            names = []
        else:
            raise DistutilsFileError(
                  "error listing files in '%s': %s" % (src, errstr))

    if not dry_run:
        mkpath(dst)

    outputs = []

    for n in names:
        src_name = os.path.join(src, n)
        dst_name = os.path.join(dst, n)
        if (condition is not None) and (not condition(src_name)):
            continue

        if preserve_symlinks and zipio.islink(src_name):
            link_dest = zipio.readlink(src_name)
            log.info("linking %s -> %s", dst_name, link_dest)
            if not dry_run:
                if update and not newer(src, dst_name):
                    pass
                else:
                    if os.path.islink(dst_name):
                        os.remove(dst_name)
                    os.symlink(link_dest, dst_name)
            outputs.append(dst_name)

        elif zipio.isdir(src_name) and not os.path.isfile(src_name):
            # ^^^ this odd tests ensures that resource files that
            # happen to be a zipfile won't get extracted.
            # XXX: need API in zipio to clean up this code
            outputs.extend(
                copy_tree(src_name, dst_name, preserve_mode,
                          preserve_times, preserve_symlinks, update,
                          dry_run=dry_run, condition=condition))
        else:
            copy_file(src_name, dst_name, preserve_mode,
                      preserve_times, update, dry_run=dry_run)
            outputs.append(dst_name)

    return outputs


def walk_files(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            yield f

def find_app(app):
    dpath = os.path.realpath(app)
    if os.path.exists(dpath):
        return dpath
    if os.path.isabs(app):
        return None
    for path in os.environ.get('PATH', '').split(':'):
        dpath = os.path.realpath(os.path.join(path, app))
        if os.path.exists(dpath):
            return dpath
    return None

def check_output(command_line):
    p = subprocess.Popen(command_line,
            stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    xit = p.wait()
    if xit != 0:
        raise subprocess.CalledProcessError(xit, command_line)

    return stdout


_tools = {}
def _get_tool(toolname):
    if toolname not in _tools:
        if os.path.exists('/usr/bin/xcrun'):
            try:
                _tools[toolname] = check_output(['/usr/bin/xcrun', '-find', toolname])[:-1]
            except subprocess.CalledProcessError:
                raise IOError("Tool %r not found"%(toolname,))

        else:
            # Support for Xcode 3.x and earlier
            if toolname == 'momc':
                choices = [
                    '/Library/Application Support/Apple/Developer Tools/Plug-ins/XDCoreDataModel.xdplugin/Contents/Resources/momc',
                    '/Developer/Library/Xcode/Plug-ins/XDCoreDataModel.xdplugin/Contents/Resources/momc',
                    '/Developer/usr/bin/momc',
                ]
            elif toolname == 'mapc':
                choices = [
                    '/Developer/Library/Xcode/Plug-ins/XDMappingModel.xdplugin/Contents/Resources/mapc'
                    '/Developer/usr/bin/mapc'
                ]
            else:
                raise IOError("Tool %r not found"%(toolname,))

            for fn in choices:
                if os.path.exists(fn):
                    _tools[toolname] = fn
                    break
            else:
                raise IOError("Tool %r not found"%(toolname,))
    return _tools[toolname]


def momc(src, dst):
    subprocess.check_call([_get_tool('momc'), src, dst])

def mapc(src, dst):
    subprocess.check_call([_get_tool('mapc'), src, dst])
