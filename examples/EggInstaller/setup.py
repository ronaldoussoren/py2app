"""
Script for building the example.

Usage:
    python setup.py py2app
"""
from setuptools import setup

PLIST = {
    "CFBundleIdentifier": "org.pythonmac.py2app.EggInstaller",
    "CFBundleDocumentTypes": [
        {
            "CFBundleTypeExtensions": ["egg"],
            "CFBundleTypeIconFile": "Egg.icns",
            "CFBundleTypeRole": "Shell",
        }
    ],
}

setup(
    setup_requires=["py2app"],
    app=["EggInstaller.py"],
    options={
        "py2app": {
            "semi_standalone": True,
            "site_packages": True,
            "argv_emulation": True,
            "iconfile": "Egg.icns",
            "plist": PLIST,
        }
    },
)
