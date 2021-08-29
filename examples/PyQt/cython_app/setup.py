""""
Usage:
    python setup.py py2app


This example uses a Cython extension what defines
the GUI mainloop. Because Cython generates a C extension
the imports in that extension are hidden from py2app's
dependency generator. The options dictionary therefore
contains an "includes" option to tell py2app about the
dependency.
"""

from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext


setup(
    name='test',
    # Include additional files into the package using MANIFEST.in
    include_package_data=True,
    app= ['main.py'],
    data_files=[],
    cmdclass = {'build_ext': build_ext},
    ext_modules = cythonize(["testLoad.pyx"], language_level=3),

    setup_requires=['py2app'],
    options={
             'cython': {"language_level":"3"},
             'py2app': {"includes": "PyQt6.QWidget"}
            },
    install_requires=[
        "Cython"
    ],
    entry_points={
        "console_scripts": [
            "testLoad = __main__:main"
        ]
    },
)
