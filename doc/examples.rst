Example setup.py templates
==========================

Basic
-----

The simplest possible ``setup.py`` script to build a py2app application
looks like the following::

    """
    py2app build script for MyApplication

    Usage:
        python setup.py py2app
    """
    from setuptools import setup
    setup(
        app=["MyApplication.py"],
    setup_requires=["py2app"],
    )

The :doc:`py2applet` script can create ``setup.py`` files of this variety
for you automatically::

    $ py2applet --make-setup MyApplication.py


Cross-platform
--------------

Cross-platform applications can share a ``setup.py`` script for both
`py2exe`_ and py2app. Here is an example 
``setup.py`` that will build an application on Windows or Mac OS X::

    """
    py2app/py2exe build script for MyApplication.

    Will automatically ensure that all build prerequisites are available
    via ez_setup

    Usage (Mac OS X):
        python setup.py py2app

    Usage (Windows):
        python setup.py py2exe
    """
    import sys
    from setuptools import setup
    
    mainscript = 'MyApplication.py'

    if sys.platform == 'darwin':
        extra_options = dict(
	    setup_requires=['py2app'],
	    app=[mainscript],
	    # Cross-platform applications generally expect sys.argv to
	    # be used for opening files.
            # Don't use this with GUI toolkits, the argv
            # emulator causes problems and toolkits generally have
            # hooks for responding to file-open events.
	    options=dict(py2app=dict(argv_emulation=True)),
	)
    elif sys.platform == 'win32':
        extra_options = dict(
	    setup_requires=['py2exe'],
	    app=[mainscript],
	)
   else:
        extra_options = dict(
	    # Normally unix-like platforms will use "setup.py install"
	    # and install the main script as such
	    scripts=[mainscript],
	)

   setup(
       name="MyApplication",
       **extra_options
   )

.. _`setuptools`: http://pypi.python.org/pypi/setuptools/
.. _`py2exe`: http://pypi.python.org/pypi/py2exe/
