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


Self-bootstrapping
------------------

For ease of distribution, you may wish to have your ``setup.py`` script
automatically ensure that `setuptools`_ is installed. This requires having a
copy of ``ez_setup`` in your project, which can be obtained from here::

    http://peak.telecommunity.com/dist/ez_setup.py

Or it may be referenced from ``svn:externals`` as such::

    ez_setup svn://svn.eby-sarna.com/svnroot/ez_setup

If choosing the ``svn:externals`` approach you should consider that your
project's source code will depend on a third party, which has reliability
and security implications. Also note that the ``ez_setup`` external uses
the ``svn://`` protocol (TCP port 3690) rather than ``http://`` so it is
somewhat less likely to work behind some firewalls or proxies.

Once this is done, you simply add the two line ``ez_setup`` preamble to the
very beginning of your ``setup.py``::

    """
    py2app build script for MyApplication.

    Will automatically ensure that all build prerequisites are available
    via ez_setup.

    Usage:
        python setup.py py2app
    """
    import ez_setup
    ez_setup.use_setuptools()

    from setuptools import setup
    setup(
        app=["MyApplication.py"],
    setup_requires=["py2app"],
    )


Cross-platform
--------------

Cross-platform applications can share a ``setup.py`` script for both
`py2exe`_ and py2app. Here is an example `Self-bootstrapping`_
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
    import ez_setup
    ez_setup.use_setuptools()

    import sys
    from setuptools import setup
    
    mainscript = 'MyApplication.py'

    if sys.platform == 'darwin':
        extra_options = dict(
	    setup_requires=['py2app'],
	    app=[mainscript],
	    # Cross-platform applications generally expect sys.argv to
	    # be used for opening files.
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