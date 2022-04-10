"""
Append module search paths for third-party packages to sys.path.

This is stripped down and customized for use in py2app applications
"""

import sys

# os is actually in the zip, so we need to do this here.
# we can't call it python24.zip because zlib is not a built-in module (!)
_libdir = "/lib/python" + sys.version[:3]
_parent = "/".join(__file__.split("/")[:-1])
if not _parent.endswith(_libdir):
    _parent += _libdir
sys.path.append(_parent + "/site-packages.zip")

# Stuffit decompresses recursively by default, that can mess up py2app bundles,
# add the uncompressed site-packages to the path to compensate for that.
sys.path.append(_parent + "/site-packages")

ENABLE_USER_SITE = False

USER_SITE = None
USER_BASE = None


def _import_os():
    global os
    import os  # noqa: E402


_import_os()

try:
    basestring
except NameError:
    basestring = str


def makepath(*paths):
    dirname = os.path.abspath(os.path.join(*paths))
    return dirname, os.path.normcase(dir)


for m in sys.modules.values():
    f = getattr(m, "__file__", None)
    if isinstance(f, basestring) and os.path.exists(f):
        m.__file__ = os.path.abspath(m.__file__)
del m

# This ensures that the initial path provided by the interpreter contains
# only absolute pathnames, even if we're running from the build directory.
L = []
_dirs_in_sys_path = {}
dirname = dircase = None  # sys.path may be empty at this point
for dirname in sys.path:
    # Filter out duplicate paths (on case-insensitive file systems also
    # if they only differ in case); turn relative paths into absolute
    # paths.
    dirname, dircase = makepath(dirname)
    if dircase not in _dirs_in_sys_path:
        L.append(dirname)
        _dirs_in_sys_path[dircase] = 1

sys.path[:] = L
del dirname, dircase, L
_dirs_in_sys_path = None


def _init_pathinfo():
    global _dirs_in_sys_path
    _dirs_in_sys_path = d = {}
    for dirname in sys.path:
        if dirname and not os.path.isdir(dirname):
            continue
        dirname, dircase = makepath(dirname)
        d[dircase] = 1


def addsitedir(sitedir):
    global _dirs_in_sys_path
    if _dirs_in_sys_path is None:
        _init_pathinfo()
        reset = 1
    else:
        reset = 0
    sitedir, sitedircase = makepath(sitedir)
    if sitedircase not in _dirs_in_sys_path:
        sys.path.append(sitedir)  # Add path component
    try:
        names = os.listdir(sitedir)
    except os.error:
        return
    names.sort()
    for name in names:
        if name[-4:] == os.extsep + "pth":
            addpackage(sitedir, name)
    if reset:
        _dirs_in_sys_path = None


def addpackage(sitedir, name):
    global _dirs_in_sys_path
    if _dirs_in_sys_path is None:
        _init_pathinfo()
        reset = 1
    else:
        reset = 0
    fullname = os.path.join(sitedir, name)
    try:
        with open(fullname) as f:
            while 1:
                dirname = f.readline()
                if not dirname:
                    break
                if dirname[0] == "#":
                    continue
                if dirname.startswith("import"):
                    exec(dirname)
                    continue
                if dirname[-1] == "\n":
                    dirname = dirname[:-1]
                dirname, dircase = makepath(sitedir, dirname)
                if dircase not in _dirs_in_sys_path and os.path.exists(dirname):
                    sys.path.append(dirname)
                    _dirs_in_sys_path[dircase] = 1
    except OSError:
        return
    if reset:
        _dirs_in_sys_path = None


def _get_path(userbase):
    version = sys.version_info

    if sys.platform == "darwin" and getattr(sys, "_framework", None):
        return f"{userbase}/lib/python/site-packages"

    return "%s/lib/python%d.%d/site-packages" % (userbase, version[0], version[1])


def _getuserbase():
    env_base = os.environ.get("PYTHONUSERBASE", None)
    if env_base:
        return env_base

    def joinuser(*args):
        return os.path.expanduser(os.path.join(*args))

    if getattr(sys, "_framework", None):
        return joinuser("~", "Library", sys._framework, "%d.%d" % sys.version_info[:2])

    return joinuser("~", ".local")


def getuserbase():
    """Returns the `user base` directory path.

    The `user base` directory can be used to store data. If the global
    variable ``USER_BASE`` is not initialized yet, this function will also set
    it.
    """
    global USER_BASE
    if USER_BASE is None:
        USER_BASE = _getuserbase()
    return USER_BASE


def getusersitepackages():
    """Returns the user-specific site-packages directory path.

    If the global variable ``USER_SITE`` is not initialized yet, this
    function will also set it.
    """
    global USER_SITE
    userbase = getuserbase()  # this will also set USER_BASE

    if USER_SITE is None:
        USER_SITE = _get_path(userbase)

    return USER_SITE


#
# Run custom site specific code, if available.
#
try:
    import sitecustomize  # noqa: F401
except ImportError:
    pass

#
# Remove sys.setdefaultencoding() so that users cannot change the
# encoding after initialization.  The test for presence is needed when
# this module is run as a script, because this code is executed twice.
#
if hasattr(sys, "setdefaultencoding"):
    del sys.setdefaultencoding

import builtins  # noqa: E402

import _sitebuiltins  # noqa: E402

builtins.help = _sitebuiltins._Helper()
builtins.quit = _sitebuiltins.Quitter("quit", "Ctrl-D (i.e. EOF)")
builtins.exit = _sitebuiltins.Quitter("exit", "Ctrl-D (i.e. EOF)")
