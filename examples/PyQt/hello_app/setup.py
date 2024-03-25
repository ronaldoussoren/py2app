"""
Script for building the example.

Usage:
    python setup.py py2app
"""

from distutils.core import setup

setup(
    setup_requires=["py2app", "PyQt5"],
    app=["hello.py"],
)
