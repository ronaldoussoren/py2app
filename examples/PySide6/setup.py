"""
Script for building the example.

Usage:
    python setup.py py2app
"""

from setuptools import setup

OPTIONS = {}

setup(
    app=["hello.py"],
    options={"py2app": OPTIONS},
)
