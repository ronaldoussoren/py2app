#!/usr/bin/env python


import os
import sys
import unittest
from distutils import log
from fnmatch import fnmatch

from setuptools import Command, find_packages, setup
from setuptools.command import egg_info

fp = open("README.rst")
try:
    LONG_DESCRIPTION = fp.read()
finally:
    fp.close()

fp = open("doc/changelog.rst")
try:
    LONG_DESCRIPTION += "\n" + fp.read()
finally:
    fp.close()

CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Environment :: MacOS X :: Cocoa",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: MacOS :: MacOS X",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Objective C",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: User Interfaces",
    "Topic :: Software Development :: Build Tools",
]


def test_loader():
    topdir = os.path.dirname(os.path.abspath(__file__))
    testModules = [
        fn[:-3]
        for fn in os.listdir(os.path.join(topdir, "py2app_tests"))
        if fn.endswith(".py")
    ]
    sys.path.insert(0, os.path.join(topdir, "py2app_tests"))

    suites = []
    for modName in testModules:
        try:
            module = __import__(modName)
        except ImportError:
            print("SKIP %s: %s" % (modName, sys.exc_info()[1]))
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

    for rootpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fnmatch(fn, pathPattern):
                result.append(os.path.join(rootpath, fn))
    return result


def importExternalTestCases(unittest, pathPattern="test_*.py", root=".", package=None):
    """
    Import all unittests in the PyObjC tree starting at 'root'
    """

    testFiles = recursiveGlob(root, pathPattern)
    testModules = map(
        lambda x: x[len(root) + 1 : -3].replace("/", "."), testFiles  # noqa: E203
    )
    if package is not None:
        testModules = [(package + "." + m) for m in testModules]

    suites = []

    for modName in testModules:
        try:
            module = __import__(modName)
        except ImportError:
            print("SKIP %s: %s" % (modName, sys.exc_info()[1]))
            continue

        if "." in modName:
            for elem in modName.split(".")[1:]:
                module = getattr(module, elem)

        s = unittest.defaultTestLoader.loadTestsFromModule(module)
        suites.append(s)

    return unittest.TestSuite(suites)


class my_egg_info(egg_info.egg_info):
    def run(self):
        egg_info.egg_info.run(self)

        path = os.path.join(self.egg_info, "PKG-INFO")
        with open(path) as fp:
            contents = fp.read()

        first, middle, last = contents.partition("\n\n")

        with open(path, "w") as fp:
            fp.write(first)
            fp.write(
                "Project-URL: Documentation, "
                "https://py2app.readthedocs.io/en/latest/\n"
            )
            fp.write(
                "Project-URL: Issue tracker, "
                "https://github.com/ronaldoussoren/py2app/issues\n"
            )
            fp.write(
                "Project-URL: Repository, " "https://github.com/ronaldoussoren/py2app\n"
            )
            fp.write(middle)
            fp.write(last)



class test(Command):
    description = "run test suite"
    user_options = [
        ("verbosity=", None, "print what tests are run"),
    ]

    def initialize_options(self):
        self.verbosity = "1"

    def finalize_options(self):
        if isinstance(self.verbosity, str):
            self.verbosity = int(self.verbosity)

    def cleanup_environment(self):
        ei_cmd = self.get_finalized_command("egg_info")
        egg_name = ei_cmd.egg_name.replace("-", "_")

        to_remove = []
        for dirname in sys.path:
            bn = os.path.basename(dirname)
            if bn.startswith(egg_name + "-"):
                to_remove.append(dirname)

        for dirname in to_remove:
            log.info("removing installed %r from sys.path before testing" % (dirname,))
            sys.path.remove(dirname)

    def add_project_to_sys_path(self):
        from pkg_resources import (
            add_activation_listener,
            normalize_path,
            require,
            working_set,
        )

        self.reinitialize_command("egg_info")
        self.run_command("egg_info")

        # Check if this distribution is already on sys.path
        # and remove that version, this ensures that the right
        # copy of the package gets tested.

        self.__old_path = sys.path[:]
        self.__old_modules = sys.modules.copy()

        ei_cmd = self.get_finalized_command("egg_info")
        sys.path.insert(0, normalize_path(ei_cmd.egg_base))
        sys.path.insert(1, os.path.dirname(__file__))

        # Strip the namespace packages defined in this distribution
        # from sys.modules, needed to reset the search path for
        # those modules.

        nspkgs = getattr(self.distribution, "namespace_packages", None)
        if nspkgs is not None:
            for nm in nspkgs:
                del sys.modules[nm]

        # Reset pkg_resources state:
        add_activation_listener(lambda dist: dist.activate())
        working_set.__init__()
        require("%s==%s" % (ei_cmd.egg_name, ei_cmd.egg_version))

    def remove_from_sys_path(self):
        from pkg_resources import working_set

        sys.path[:] = self.__old_path
        sys.modules.clear()
        sys.modules.update(self.__old_modules)
        working_set.__init__()

    def run(self):
        if sys.version_info[:2] <= (2, 6):
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
            suite = importExternalTestCases(unittest, "test_*.py", test_pkg, test_pkg)

            runner = unittest.TextTestRunner(verbosity=self.verbosity)
            result = runner.run(suite)

            # Print out summary. This is a structured format that
            # should make it easy to use this information in scripts.
            summary = {
                "count": result.testsRun,
                "fails": len(result.failures),
                "errors": len(result.errors),
                "xfails": len(getattr(result, "expectedFailures", [])),
                "xpass": len(getattr(result, "expectedSuccesses", [])),
                "skip": len(getattr(result, "skipped", [])),
            }
            print("SUMMARY: %s" % (summary,))
            if summary["fails"] or summary["errors"]:
                sys.exit(1)

        finally:
            self.remove_from_sys_path()


cmdclass = {"egg_info": my_egg_info, "test": test}
if sys.platform != "darwin":
    msg = "This distribution is only supported on MacOSX"
    from distutils.command import build, install
    from distutils.errors import DistutilsPlatformError

    from setuptools.command import build_py, develop, install_lib

    def create_command_subclass(base_class):
        class subcommand(base_class):
            def run(self):
                raise DistutilsPlatformError(msg)

        return subcommand

    class no_test(test):
        def run(self):
            print("WARNING: %s\n" % (msg,))
            print(
                "SUMMARY: {'count': 0, 'fails': 0, 'errors': 0, "
                "'xfails': 0, 'skip': 65, 'xpass': 0, 'message': msg }\n"
            )

    cmdclass["build"] = create_command_subclass(build.build)
    cmdclass["test"] = no_test
    cmdclass["install"] = create_command_subclass(install.install)
    cmdclass["install_lib"] = create_command_subclass(install_lib.install_lib)
    cmdclass["develop"] = create_command_subclass(develop.develop)
    cmdclass["build_py"] = create_command_subclass(build_py.build_py)

setup(
    # metadata
    name="py2app",
    version="0.28.2",
    description="Create standalone Mac OS X applications with Python",
    # author='Bob Ippolito',
    # author_email='bob@redivi.com',
    author="Ronald Oussoren",
    author_email="ronaldoussoren@mac.com",
    maintainer="Ronald Oussoren",
    maintainer_email="ronaldoussoren@mac.com",
    url="http://github.com/ronaldoussoren/py2app",
    download_url="http://pypi.python.org/pypi/py2app",
    license="MIT or PSF License",
    platforms=["MacOS X"],
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/x-rst; charset=UTF-8",
    classifiers=CLASSIFIERS,
    keywords=[".app", "standalone"],
    install_requires=["altgraph>=0.16", "modulegraph>=0.17", "macholib>=1.16"],
    setup_requires=["altgraph>=0.16", "modulegraph>=0.17", "macholib>=1.16"],
    tests_require=["pyobjc"],
    cmdclass=cmdclass,
    packages=find_packages(exclude=["py2app_tests"]),
    package_data={
        "py2app.recipes": ["qt.conf"],
        "py2app.apptemplate": [
            "prebuilt/main-arm64",
            "prebuilt/main-i386",
            "prebuilt/main-ppc",
            "prebuilt/main-x86_64",
            "prebuilt/main-x86_64-oldsdk",
            "prebuilt/main-ppc64",
            "prebuilt/main-fat",
            "prebuilt/main-fat3",
            "prebuilt/main-intel",
            "prebuilt/main-universal",
            "prebuilt/main-universal2",
            "prebuilt/main-asl-arm64",
            "prebuilt/main-asl-i386",
            "prebuilt/main-asl-ppc",
            "prebuilt/main-asl-x86_64",
            "prebuilt/main-asl-ppc64",
            "prebuilt/main-asl-fat",
            "prebuilt/main-asl-fat3",
            "prebuilt/main-asl-intel",
            "prebuilt/main-asl-universal",
            "prebuilt/main-asl-universal2",
            "prebuilt/secondary-arm64",
            "prebuilt/secondary-i386",
            "prebuilt/secondary-ppc",
            "prebuilt/secondary-x86_64",
            "prebuilt/secondary-x86_64-oldsdk",
            "prebuilt/secondary-ppc64",
            "prebuilt/secondary-fat",
            "prebuilt/secondary-fat3",
            "prebuilt/secondary-intel",
            "prebuilt/secondary-universal",
            "prebuilt/secondary-universal2",
            "lib/__error__.sh",
            "lib/site.py",
            "src/main.c",
        ],
        "py2app.bundletemplate": [
            "prebuilt/main-arm64",
            "prebuilt/main-i386",
            "prebuilt/main-ppc",
            "prebuilt/main-x86_64",
            "prebuilt/main-ppc64",
            "prebuilt/main-fat",
            "prebuilt/main-fat3",
            "prebuilt/main-intel",
            "prebuilt/main-universal",
            "prebuilt/main-universal2",
            "lib/__error__.sh",
            "lib/site.py",
            "src/main.m",
        ],
    },
    entry_points={
        "setuptools.finalize_distribution_options": [
            "py2app = py2app.build_app:finalize_distribution_options"
        ],
        "distutils.commands": ["py2app = py2app.build_app:py2app"],
        "distutils.setup_keywords": [
            "app =    py2app.build_app:validate_target",
            "plugin = py2app.build_app:validate_target",
        ],
        "console_scripts": ["py2applet = py2app.script_py2applet:main"],
        "py2app.converter": [
            "xib          = py2app.converters.nibfile:convert_xib",
            "datamodel    = py2app.converters.coredata:convert_datamodel",
            "mappingmodel = py2app.converters.coredata:convert_mappingmodel",
        ],
        "py2app.recipe": [],
    },
    # py2app/build_app.py uses imp.find_module, and that won't work
    # with a zipped egg.
    zip_safe=False,
    dependency_links=[],  # workaround for setuptools 0.6b4 bug
)
