from setuptools import setup

APP = ['main.py']
DATA_FILES = ['main.qml']
OPTIONS = {'argv_emulation': False}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app', 'PyQt5'],
)
