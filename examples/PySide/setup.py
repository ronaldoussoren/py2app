"""
Script for building the example.

Usage:
    python setup.py py2app
"""
from distutils.core import setup
import py2app


OPTIONS = {'arch': 'i386', 'argv_emulation': True, 'includes': 'wx',
                            'plist' : {
                                        'LSPrefersPPC' : False,
                                        'LSArchitecturePriority' : ['i386'],
                                        'CFBundleIdentifier' : 'com.saveon.placefind',
                                        'CFBundleName' : 'PlaceFind',
                                        'CFBundleDisplayName' : 'PlaceFind',
                                        'CFBundleVersion' : '14.03.01'
                            }
            }

setup(
    app=["hello.py"],
    options={'py2app': OPTIONS},
)
