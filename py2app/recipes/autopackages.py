import os

AUTO_PACKAGES=[
    # Embbedded datafiles accessed using 
    # ``__file__`` relative paths.
    'botocore',
    
    # Import dependencies between C extensions
    'h5py',

    # pycyptodome contains C libraries
    # that are loaded using ctypes and are
    # not detected by the regular machinery.
    # Just bail out and include this package
    # completely and in the filesystem.
    'Crypto',

    # PyZMQ is a package that contains
    # a shared library.
    # XXX: Check if this is still needed.
    'zmq',

    # Various
    'numpy',
    'scipy',
    'tensorflow',

]

def check(cmd, mf):
    to_include = []
    for python_package in AUTO_PACKAGES:
        m = mf.findNode(python_package)
        if m is None or m.filename is None:
            return None

        to_include.append(python_package)

    if to_include:
        return { "packages": to_include }
    return None
