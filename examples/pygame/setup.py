"""
Script for building the example.

Usage:
    python setup.py py2app
"""
from setuptools import setup

NAME = 'aliens'
VERSION = '0.1'

plist = dict(
    CFBundleIconFile=NAME,
    CFBundleName=NAME,
    CFBundleShortVersionString=VERSION,
    CFBundleGetInfoString=' '.join([NAME, VERSION]),
    CFBundleExecutable=NAME,
    CFBundleIdentifier='org.pygame.examples.aliens',
)

setup(
    data_files=['English.lproj', 'data'],
    app=["aliens.py"],
    setup_requires=["py2app"],
    options=dict(
        py2app=dict(
            plist=plist,
        )
    )
)
