#!/usr/bin/env python


#
#
#
# Bootstrapping setuptools/distribute, based on
# a heavily modified version of distribute_setup.py
#
#
#
import os
import sys
try:
    import urllib.request as urllib
except ImportError:
    import urllib

import tempfile
import tarfile
from distutils import log
try:
    from hashlib import md5

except ImportError:
    from md5 import md5



SETUPTOOLS_PACKAGE='setuptools'


try:
    import subprocess

    def _python_cmd(*args):
        args = (sys.executable,) + args
        return subprocess.call(args) == 0

except ImportError:
    def _python_cmd(*args):
        args = (sys.executable,) + args
        new_args = []
        for a in args:
            new_args.append(a.replace("'", "'\"'\"'"))
        os.system(' '.join(new_args)) == 0


try:
    import json

    def get_pypi_src_download(package):
        url = 'https://pypi.python.org/pypi/%s/json'%(package,)
        fp = urllib.urlopen(url)
        try:
            try:
                data = fp.read()

            finally:
                fp.close()
        except urllib.error:
            raise RuntimeError("Cannot determine download link for %s"%(package,))

        pkgdata = json.loads(data.decode('utf-8'))
        if 'urls' not in pkgdata:
            raise RuntimeError("Cannot determine download link for %s"%(package,))

        for info in pkgdata['urls']:
            if info['packagetype'] == 'sdist' and info['url'].endswith('tar.gz'):
                return (info.get('md5_digest'), info['url'])

        raise RuntimeError("Cannot determine downlink link for %s"%(package,))

except ImportError:
    # Python 2.5 compatibility, no JSON in stdlib but luckily JSON syntax is
    # simular enough to Python's syntax to be able to abuse the Python compiler

    import _ast as ast

    def get_pypi_src_download(package):
        url = 'https://pypi.python.org/pypi/%s/json'%(package,)
        fp = urllib.urlopen(url)
        try:
            try:
                data = fp.read()

            finally:
                fp.close()
        except urllib.error:
            raise RuntimeError("Cannot determine download link for %s"%(package,))


        a = compile(data, '-', 'eval', ast.PyCF_ONLY_AST)
        if not isinstance(a, ast.Expression):
            raise RuntimeError("Cannot determine download link for %s"%(package,))

        a = a.body
        if not isinstance(a, ast.Dict):
            raise RuntimeError("Cannot determine download link for %s"%(package,))

        for k, v in zip(a.keys, a.values):
            if not isinstance(k, ast.Str):
                raise RuntimeError("Cannot determine download link for %s"%(package,))

            k = k.s
            if k == 'urls':
                a = v
                break
        else:
            raise RuntimeError("PyPI JSON for %s doesn't contain URLs section"%(package,))

        if not isinstance(a, ast.List):
            raise RuntimeError("Cannot determine download link for %s"%(package,))

        for info in v.elts:
            if not isinstance(info, ast.Dict):
                raise RuntimeError("Cannot determine download link for %s"%(package,))
            url = None
            packagetype = None
            chksum = None

            for k, v in zip(info.keys, info.values):
                if not isinstance(k, ast.Str):
                    raise RuntimeError("Cannot determine download link for %s"%(package,))

                if k.s == 'url':
                    if not isinstance(v, ast.Str):
                        raise RuntimeError("Cannot determine download link for %s"%(package,))
                    url = v.s

                elif k.s == 'packagetype':
                    if not isinstance(v, ast.Str):
                        raise RuntimeError("Cannot determine download link for %s"%(package,))
                    packagetype = v.s

                elif k.s == 'md5_digest':
                    if not isinstance(v, ast.Str):
                        raise RuntimeError("Cannot determine download link for %s"%(package,))
                    chksum = v.s

            if url is not None and packagetype == 'sdist' and url.endswith('.tar.gz'):
                return (chksum, url)

        raise RuntimeError("Cannot determine download link for %s"%(package,))

def _build_egg(egg, tarball, to_dir):
    # extracting the tarball
    tmpdir = tempfile.mkdtemp()
    log.warn('Extracting in %s', tmpdir)
    old_wd = os.getcwd()
    try:
        os.chdir(tmpdir)
        tar = tarfile.open(tarball)
        _extractall(tar)
        tar.close()

        # going in the directory
        subdir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        os.chdir(subdir)
        log.warn('Now working in %s', subdir)

        # building an egg
        log.warn('Building a %s egg in %s', egg, to_dir)
        _python_cmd('setup.py', '-q', 'bdist_egg', '--dist-dir', to_dir)

    finally:
        os.chdir(old_wd)
    # returning the result
    log.warn(egg)
    if not os.path.exists(egg):
        raise IOError('Could not build the egg.')


def _do_download(to_dir, packagename=SETUPTOOLS_PACKAGE):
    tarball = download_setuptools(packagename, to_dir)
    version = tarball.split('-')[-1][:-7]
    egg = os.path.join(to_dir, '%s-%s-py%d.%d.egg'
                       % (packagename, version, sys.version_info[0], sys.version_info[1]))
    if not os.path.exists(egg):
        _build_egg(egg, tarball, to_dir)
    sys.path.insert(0, egg)
    import setuptools
    setuptools.bootstrap_install_from = egg


def use_setuptools():
    # making sure we use the absolute path
    return _do_download(os.path.abspath(os.curdir))

def download_setuptools(packagename, to_dir):
    # making sure we use the absolute path
    to_dir = os.path.abspath(to_dir)
    try:
        from urllib.request import urlopen
    except ImportError:
        from urllib2 import urlopen

    chksum, url = get_pypi_src_download(packagename)
    tgz_name = os.path.basename(url)
    saveto = os.path.join(to_dir, tgz_name)

    src = dst = None
    if not os.path.exists(saveto):  # Avoid repeated downloads
        try:
            log.warn("Downloading %s", url)
            src = urlopen(url)
            # Read/write all in one block, so we don't create a corrupt file
            # if the download is interrupted.
            data = src.read()

            if chksum is not None:
                data_sum = md5(data).hexdigest()
                if data_sum != chksum:
                    raise RuntimeError("Downloading %s failed: corrupt checksum"%(url,))


            dst = open(saveto, "wb")
            dst.write(data)
        finally:
            if src:
                src.close()
            if dst:
                dst.close()
    return os.path.realpath(saveto)



def _extractall(self, path=".", members=None):
    """Extract all members from the archive to the current working
       directory and set owner, modification time and permissions on
       directories afterwards. `path' specifies a different directory
       to extract to. `members' is optional and must be a subset of the
       list returned by getmembers().
    """
    import copy
    import operator
    from tarfile import ExtractError
    directories = []

    if members is None:
        members = self

    for tarinfo in members:
        if tarinfo.isdir():
            # Extract directories with a safe mode.
            directories.append(tarinfo)
            tarinfo = copy.copy(tarinfo)
            tarinfo.mode = 448 # decimal for oct 0700
        self.extract(tarinfo, path)

    # Reverse sort directories.
    if sys.version_info < (2, 4):
        def sorter(dir1, dir2):
            return cmp(dir1.name, dir2.name)
        directories.sort(sorter)
        directories.reverse()
    else:
        directories.sort(key=operator.attrgetter('name'), reverse=True)

    # Set correct owner, mtime and filemode on directories.
    for tarinfo in directories:
        dirpath = os.path.join(path, tarinfo.name)
        try:
            self.chown(tarinfo, dirpath)
            self.utime(tarinfo, dirpath)
            self.chmod(tarinfo, dirpath)
        except ExtractError:
            e = sys.exc_info()[1]
            if self.errorlevel > 1:
                raise
            else:
                self._dbg(1, "tarfile: %s" % e)



try:
    import setuptools
except ImportError:
    use_setuptools()


import sys, os
from setuptools import setup, find_packages
from distutils.errors  import DistutilsError
from distutils import log
from distutils.core import Command
from fnmatch import fnmatch
from setuptools.command import egg_info

fp = open('README.txt')
try:
    LONG_DESCRIPTION = fp.read()
finally:
    fp.close()

fp = open('doc/changelog.rst')
try:
    LONG_DESCRIPTION += '\n' + fp.read()
finally:
    fp.close()

CLASSIFIERS = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: MacOS X :: Cocoa',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Objective C',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Build Tools',
]


if sys.version_info[0] == 3 or (sys.version_info[:2] >= (2,7)):
    tests_require = [ 'pyobjc']
else:
    tests_require = ['unittest2', 'pyobjc' ]





def test_loader():

    if sys.version_info[0] == 3 or sys.version_info[:2] >= (2, 7):
        import unittest
    else:
        import unittest2 as unittest

    topdir = os.path.dirname(os.path.abspath(__file__))
    testModules = [ fn[:-3] for fn in os.listdir(os.path.join(topdir, 'py2app_tests')) if fn.endswith('.py')]
    sys.path.insert(0, os.path.join(topdir, 'py2app_tests'))

    suites = []
    for modName in testModules:
        try:
            module = __import__(modName)
        except ImportError:
            print ("SKIP %s: %s"%(modName, sys.exc_info()[1]))
            continue

        s = unittest.defaultTestLoader.loadTestsFromModule(module)
        suites.append(s)

    return unittest.TestSuite(suites)


def recursiveGlob(root, pathPattern):
    """
    Recursively look for files matching 'pathPattern'. Return a list
    of matching files/directories.
    """
    result = []

    for rootpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fnmatch(fn, pathPattern):
                result.append(os.path.join(rootpath, fn))
    return result


def importExternalTestCases(unittest,
        pathPattern="test_*.py", root=".", package=None):
    """
    Import all unittests in the PyObjC tree starting at 'root'
    """

    testFiles = recursiveGlob(root, pathPattern)
    testModules = map(lambda x:x[len(root)+1:-3].replace('/', '.'), testFiles)
    if package is not None:
        testModules = [(package + '.' + m) for m in testModules]

    suites = []

    for modName in testModules:
        try:
            module = __import__(modName)
        except ImportError:
            print("SKIP %s: %s"%(modName, sys.exc_info()[1]))
            continue

        if '.' in modName:
            for elem in modName.split('.')[1:]:
                module = getattr(module, elem)

        s = unittest.defaultTestLoader.loadTestsFromModule(module)
        suites.append(s)

    return unittest.TestSuite(suites)

class my_egg_info (egg_info.egg_info):
    def run(self):
        egg_info.egg_info.run(self)

        path = os.path.join(self.egg_info, 'PKG-INFO')
        with open(path, 'a+') as fp:
            fp.write('Project-URL: Documentation, https://py2app.readthedocs.io/en/latest/\n')
            fp.write('Project-URL: Issue tracker, https://bitbucket.org/ronaldoussoren/py2app/issues?status=new&status=open\n')


class test (Command):
    description = "run test suite"
    user_options = [
        ('verbosity=', None, "print what tests are run"),
    ]

    def initialize_options(self):
        self.verbosity='1'

    def finalize_options(self):
        if isinstance(self.verbosity, str):
            self.verbosity = int(self.verbosity)


    def cleanup_environment(self):
        ei_cmd = self.get_finalized_command('egg_info')
        egg_name = ei_cmd.egg_name.replace('-', '_')

        to_remove =  []
        for dirname in sys.path:
            bn = os.path.basename(dirname)
            if bn.startswith(egg_name + "-"):
                to_remove.append(dirname)

        for dirname in to_remove:
            log.info("removing installed %r from sys.path before testing"%(
                dirname,))
            sys.path.remove(dirname)

    def add_project_to_sys_path(self):
        from pkg_resources import normalize_path, add_activation_listener
        from pkg_resources import working_set, require

        self.reinitialize_command('egg_info')
        self.run_command('egg_info')
        self.reinitialize_command('build_ext', inplace=1)
        self.run_command('build_ext')


        # Check if this distribution is already on sys.path
        # and remove that version, this ensures that the right
        # copy of the package gets tested.

        self.__old_path = sys.path[:]
        self.__old_modules = sys.modules.copy()


        ei_cmd = self.get_finalized_command('egg_info')
        sys.path.insert(0, normalize_path(ei_cmd.egg_base))
        sys.path.insert(1, os.path.dirname(__file__))

        # Strip the namespace packages defined in this distribution
        # from sys.modules, needed to reset the search path for
        # those modules.

        nspkgs = getattr(self.distribution, 'namespace_packages')
        if nspkgs is not None:
            for nm in nspkgs:
                del sys.modules[nm]

        # Reset pkg_resources state:
        add_activation_listener(lambda dist: dist.activate())
        working_set.__init__()
        require('%s==%s'%(ei_cmd.egg_name, ei_cmd.egg_version))

    def remove_from_sys_path(self):
        from pkg_resources import working_set
        sys.path[:] = self.__old_path
        sys.modules.clear()
        sys.modules.update(self.__old_modules)
        working_set.__init__()


    def run(self):
        if sys.version_info[:2] <= (2,6):
            import unittest2 as unittest
        else:
            import unittest

        # Ensure that build directory is on sys.path (py3k)

        self.cleanup_environment()
        self.add_project_to_sys_path()

        try:
            meta = self.distribution.metadata
            name = meta.get_name()
            test_pkg = name + "_tests"
            suite = importExternalTestCases(unittest,
                    "test_*.py", test_pkg, test_pkg)

            runner = unittest.TextTestRunner(verbosity=self.verbosity)
            result = runner.run(suite)

            # Print out summary. This is a structured format that
            # should make it easy to use this information in scripts.
            summary = dict(
                count=result.testsRun,
                fails=len(result.failures),
                errors=len(result.errors),
                xfails=len(getattr(result, 'expectedFailures', [])),
                xpass=len(getattr(result, 'expectedSuccesses', [])),
                skip=len(getattr(result, 'skipped', [])),
            )
            print("SUMMARY: %s"%(summary,))
            if summary['fails'] or summary['errors']:
                sys.exit(1)

        finally:
            self.remove_from_sys_path()


cmdclass = dict(
    egg_info=my_egg_info,
    test=test,
)
if sys.platform != 'darwin':
    msg = "This distribution is only supported on MacOSX"
    from distutils.command import build, install
    from setuptools.command import develop, build_ext, install_lib, build_py
    from distutils.errors import DistutilsPlatformError


    def create_command_subclass(base_class):
        class subcommand (base_class):
            def run(self):
                raise DistutilsPlatformError(msg)
        return subcommand

    class no_test (test):
        def run(self):
            print("WARNING: %s\n"%(msg,))
            print("SUMMARY: {'count': 0, 'fails': 0, 'errors': 0, 'xfails': 0, 'skip': 65, 'xpass': 0, 'message': msg }\n")

    cmdclass['build'] = create_command_subclass(build.build)
    cmdclass['test'] = no_test
    cmdclass['install'] = create_command_subclass(install.install)
    cmdclass['install_lib'] = create_command_subclass(install_lib.install_lib)
    cmdclass['develop'] = create_command_subclass(develop.develop)
    cmdclass['build_py'] = create_command_subclass(build_py.build_py)

setup(
    # metadata
    name='py2app',
    version='0.15',
    description='Create standalone Mac OS X applications with Python',
    #author='Bob Ippolito',
    #author_email='bob@redivi.com',
    author='Ronald Oussoren',
    author_email="ronaldoussoren@mac.com",
    maintainer='Ronald Oussoren',
    maintainer_email="ronaldoussoren@mac.com",
    url='http://bitbucket.org/ronaldoussoren/py2app',
    download_url='http://pypi.python.org/pypi/py2app',
    license='MIT or PSF License',
    platforms=['MacOS X'],
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst; charset=UTF-8',
    classifiers=CLASSIFIERS,
    keywords=['.app', 'standalone'],
    install_requires=[
        "altgraph>=0.16",
        "modulegraph>=0.17",
        "macholib>=1.10",
    ],
    tests_require=tests_require,
    cmdclass=cmdclass,
    packages=find_packages(exclude=['py2app_tests']),
    package_data={
        'py2app.recipes': [
            'qt.conf',
        ],
        'py2app.apptemplate': [
            'prebuilt/main-i386',
            'prebuilt/main-ppc',
            'prebuilt/main-x86_64',
            'prebuilt/main-ppc64',
            'prebuilt/main-fat',
            'prebuilt/main-fat3',
            'prebuilt/main-intel',
            'prebuilt/main-universal',
            'prebuilt/secondary-i386',
            'prebuilt/secondary-ppc',
            'prebuilt/secondary-x86_64',
            'prebuilt/secondary-ppc64',
            'prebuilt/secondary-fat',
            'prebuilt/secondary-fat3',
            'prebuilt/secondary-intel',
            'prebuilt/secondary-universal',
            'lib/__error__.sh',
            'lib/site.py',
            'src/main.c',
        ],
        'py2app.bundletemplate': [
            'prebuilt/main-i386',
            'prebuilt/main-ppc',
            'prebuilt/main-x86_64',
            'prebuilt/main-ppc64',
            'prebuilt/main-fat',
            'prebuilt/main-fat3',
            'prebuilt/main-intel',
            'prebuilt/main-universal',
            'lib/__error__.sh',
            'lib/site.py',
            'src/main.m',
        ],
    },
    entry_points={
        'distutils.commands': [
            "py2app = py2app.build_app:py2app",
        ],
        'distutils.setup_keywords': [
            "app =    py2app.build_app:validate_target",
            "plugin = py2app.build_app:validate_target",
        ],
        'console_scripts': [
            "py2applet = py2app.script_py2applet:main",
        ],
        'py2app.converter': [
            "xib          = py2app.converters.nibfile:convert_xib",
            "datamodel    = py2app.converters.coredata:convert_datamodel",
            "mappingmodel = py2app.converters.coredata:convert_mappingmodel",
        ],
        'py2app.recipe': [
        ]
    },

    # py2app/build_app.py uses imp.find_module, and that won't work
    # with a zipped egg.
    zip_safe=False,
    dependency_links=[], # workaround for setuptools 0.6b4 bug
)
