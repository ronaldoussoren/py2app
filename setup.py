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
from setuptools.command import test
try:
    from distutils.core import PyPIRCCommand
except ImportError:
    PyPIRCCommand = None
    from distutils.core import Command

LONG_DESCRIPTION = open('README.txt').read()
LONG_DESCRIPTION += '\n' + open('doc/changelog.rst').read()

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

if sys.version_info[0] == 3:
    extra_args = dict(use_2to3=True)
else:
    extra_args = dict()


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

setup(
    # metadata
    name='py2app',
    version='0.6.4',
    description='Create standalone Mac OS X applications with Python',
    author='Bob Ippolito',
    author_email='bob@redivi.com',
    maintainer='Ronald Oussoren',
    maintainer_email="ronaldoussoren@mac.com",
    url='http://bitbucket.org/ronaldoussoren/py2app',
    download_url='http://pypi.python.org/pypi/py2app',
    license='MIT or PSF License',
    platforms=['MacOS X'],
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    install_requires=[
        "altgraph>=0.9",
        "modulegraph>=0.9.1",
        "macholib>=1.4.2",
    ],
    tests_require=tests_require,
    cmdclass=dict(
        upload_docs=upload_docs,
    ),
    packages=find_packages(exclude=['py2app_tests']),
    package_data={
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
            "app = py2app.build_app:validate_target",
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
    zip_safe=False,
    dependency_links=[], # workaround for setuptools 0.6b4 bug
    test_suite='__main__.test_loader',
    **extra_args
)
