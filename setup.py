#!/usr/bin/env python

try:
    import setuptools
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()

import sys, os
from setuptools import setup, find_packages
from distutils.errors  import DistutilsError
from distutils import log
from distutils.core import Command
from fnmatch import fnmatch

try:
    from distutils.core import PyPIRCCommand
except ImportError:
    PyPIRCCommand = None

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
        'Programming Language :: Python :: 3',
        'Programming Language :: Objective C',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Build Tools',
]


if sys.version_info[0] == 3 or (sys.version_info[:2] >= (2,7)):
    tests_require = []
else:
    tests_require = ['unittest2']





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

if PyPIRCCommand is None:
    class upload_docs (Command):
        description = "upload sphinx documentation"
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            raise DistutilsError("not supported on this version of python")

else:
    class upload_docs (PyPIRCCommand):
        description = "upload sphinx documentation"
        user_options = PyPIRCCommand.user_options

        def initialize_options(self):
            PyPIRCCommand.initialize_options(self)
            self.username = ''
            self.password = ''


        def finalize_options(self):
            PyPIRCCommand.finalize_options(self)
            config = self._read_pypirc()
            if config != {}:
                self.username = config['username']
                self.password = config['password']


        def run(self):
            import subprocess
            import shutil
            import zipfile
            import os
            import urllib
            import StringIO
            from base64 import standard_b64encode
            import httplib
            import urlparse

            # Extract the package name from distutils metadata
            meta = self.distribution.metadata
            name = meta.get_name()

            # Run sphinx
            if os.path.exists('doc/_build'):
                shutil.rmtree('doc/_build')
            os.mkdir('doc/_build')

            p = subprocess.Popen(['make', 'html'],
                cwd='doc')
            exit = p.wait()
            if exit != 0:
                raise DistutilsError("sphinx-build failed")

            # Collect sphinx output
            if not os.path.exists('dist'):
                os.mkdir('dist')
            zf = zipfile.ZipFile('dist/%s-docs.zip'%(name,), 'w', 
                    compression=zipfile.ZIP_DEFLATED)

            for toplevel, dirs, files in os.walk('doc/_build/html'):
                for fn in files:
                    fullname = os.path.join(toplevel, fn)
                    relname = os.path.relpath(fullname, 'doc/_build/html')

                    print ("%s -> %s"%(fullname, relname))

                    zf.write(fullname, relname)

            zf.close()

            # Upload the results, this code is based on the distutils
            # 'upload' command.
            content = open('dist/%s-docs.zip'%(name,), 'rb').read()
            
            data = {
                ':action': 'doc_upload',
                'name': name,
                'content': ('%s-docs.zip'%(name,), content),
            }
            auth = "Basic " + standard_b64encode(self.username + ":" +
                 self.password)


            boundary = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
            sep_boundary = '\n--' + boundary
            end_boundary = sep_boundary + '--'
            body = StringIO.StringIO()
            for key, value in data.items():
                if not isinstance(value, list):
                    value = [value]

                for value in value:
                    if isinstance(value, tuple):
                        fn = ';filename="%s"'%(value[0])
                        value = value[1]
                    else:
                        fn = ''

                    body.write(sep_boundary)
                    body.write('\nContent-Disposition: form-data; name="%s"'%key)
                    body.write(fn)
                    body.write("\n\n")
                    body.write(value)

            body.write(end_boundary)
            body.write('\n')
            body = body.getvalue()

            self.announce("Uploading documentation to %s"%(self.repository,), log.INFO)

            schema, netloc, url, params, query, fragments = \
                    urlparse.urlparse(self.repository)


            if schema == 'http':
                http = httplib.HTTPConnection(netloc)
            elif schema == 'https':
                http = httplib.HTTPSConnection(netloc)
            else:
                raise AssertionError("unsupported schema "+schema)

            data = ''
            loglevel = log.INFO
            try:
                http.connect()
                http.putrequest("POST", url)
                http.putheader('Content-type',
                    'multipart/form-data; boundary=%s'%boundary)
                http.putheader('Content-length', str(len(body)))
                http.putheader('Authorization', auth)
                http.endheaders()
                http.send(body)
            except socket.error:
                e = socket.exc_info()[1]
                self.announce(str(e), log.ERROR)
                return

            r = http.getresponse()
            if r.status in (200, 301):
                self.announce('Upload succeeded (%s): %s' % (r.status, r.reason),
                    log.INFO)
            else:
                self.announce('Upload failed (%s): %s' % (r.status, r.reason),
                    log.ERROR)

                print ('-'*75) 
                print (r.read())
                print ('-'*75)


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

        finally:
            self.remove_from_sys_path()
setup(
    # metadata
    name='py2app',
    version='0.7.3',
    description='Create standalone Mac OS X applications with Python',
    #author='Bob Ippolito',
    #author_email='bob@redivi.com',
    maintainer='Ronald Oussoren',
    maintainer_email="ronaldoussoren@mac.com",
    url='http://bitbucket.org/ronaldoussoren/py2app',
    download_url='http://pypi.python.org/pypi/py2app',
    license='MIT or PSF License',
    platforms=['MacOS X'],
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    install_requires=[
        "altgraph>=0.10.1",
        "modulegraph>=0.10.3",
        "macholib>=1.5",
    ],
    tests_require=tests_require,
    cmdclass=dict(
        upload_docs=upload_docs,
        test=test,
    ),
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
    #zip_safe=False,
    dependency_links=[], # workaround for setuptools 0.6b4 bug
)
