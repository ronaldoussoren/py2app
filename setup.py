#!/usr/bin/env python

try:
    import setuptools
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()

import sys, os
from setuptools import setup, find_packages
from pkg_resources import require, DistributionNotFound

cmdclass = {}

LONG_DESCRIPTION = open('README.txt').read()

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

setup(
    # metadata
    name='py2app',
    version='0.5.3',
    description='Create standalone Mac OS X applications with Python',
    author='Bob Ippolito',
    author_email='bob@redivi.com',
    maintainer='Ronald Oussoren',
    maintainer_email="ronaldoussoren@mac.com",
    url='http://undefined.org/python/#py2app',
    download_url='http://undefined.org/python/#py2app',
    license='MIT or PSF License',
    platforms=['MacOS X'],
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    install_requires=[
        "altgraph>=0.7",
        "modulegraph>=0.8.1",
        "macholib>=1.3",
    ],

    # sources
    cmdclass=cmdclass,
    packages=find_packages(),
    package_data={
        'py2app.apptemplate': [
            'prebuilt/main-fat',
            'prebuilt/main-fat3',
            'prebuilt/main-intel',
            'prebuilt/main-universal',
            'lib/__error__.sh',
            'lib/site.py',
            'src/main.c',
        ],
        'py2app.bundletemplate': [
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
    # workaround for setuptools 0.6b4 bug
    dependency_links=[],
    **extra_args
)
