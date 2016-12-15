"""
Script for building the example.

Usage:
    python setup.py py2app
"""
from distutils.core import setup
import py2app

setup(
    setup_requires=['py2app', 'PyQt5'],
    app=["hello.py"],
)
