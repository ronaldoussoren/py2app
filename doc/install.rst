Installation
============

Installing with easy_install
----------------------------

To install py2app using `easy_install`_ you must make sure you have a recent
version of `setuptools`_ installed (as of this writing, 0.6b4 or later)::

    $ curl -O http://peak.telecommunity.com/dist/ez_setup.py
    $ sudo python ez_setup.py -U setuptools

To install or upgrade to the latest released version of py2app::

    $ sudo easy_install -U py2app


Installing from source
----------------------

To install py2app from source, simply use the normal procedure for
installing any Python package. Since py2app uses `setuptools`_,
all dependencies (including `setuptools`_ itself) will be automatically
acquired and installed for you as appropriate::

    $ python setup.py install

If you're using a svn checkout, it's recommended to use the `setuptools`_
`develop command`_, which will simply activate py2app directly from your
source directory. This way you can do a ``svn up`` or make changes to the
source code without re-installing every time::

    $ python setup.py develop


Upgrade Notes
-------------

The ``setup.py`` template has changed slightly in py2app 0.3 in order
to accommodate the enhancements brought on by `setuptools`_. Old ``setup.py``
scripts look like this::

    from distutils.core import setup
    import py2app

    setup(
        app=["myscript.py"],
    )

New py2app scripts should look like this::

    from setuptools import setup
    setup(
        app=["myscript.py"],
	setup_requires=["py2app"],
    )

.. _`setuptools`: http://pypi.python.org/pypi/setuptools/
.. _`easy_install`: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _`develop command`: http://peak.telecommunity.com/DevCenter/setuptools#development-mode