Installation
============


Installing with pip
-------------------

To installp py2app using `pip`_, or to upgrade to the latest released version
of py2app:

.. code-block:: sh

  $ pip install -U py2app

If you install into a system installation of Python you might need additional
privileges, you can use the `sudo`_ commando to get those:

.. code-block:: sh

    $ sudo pip install -U py2app


Installing with easy_install
----------------------------

To install py2app using `easy_install`_ you must make sure you have a recent
version of `distribute`_ installed (as of this writing, 0.6b4 or later):


.. code-block:: sh

    $ curl -O http://python-distribute.org/distribute_setup.py
    $ python ez_setup.py -U distribute

To install or upgrade to the latest released version of py2app:

.. code-block:: sh

    $ easy_install -U py2app

If you install into a system installation of Python you might need additional
privileges, you can use the `sudo`_ commando to get those:

.. code-block:: sh

    $ sudo easy_install -U py2app


Installing from source
----------------------

To install py2app from source, simply use the normal procedure for
installing any Python package. Since py2app uses `distribute`_,
all dependencies (including `distribute`_ itself) will be automatically
acquired and installed for you as appropriate:

.. code-block:: sh

    $ python setup.py install

If you're using a svn checkout, it's recommended to use the `distribute`_
`develop command`_, which will simply activate py2app directly from your
source directory. This way you can do a ``svn up`` or make changes to the
source code without re-installing every time:

.. code-block:: sh

    $ python setup.py develop


Upgrade Notes
-------------

The ``setup.py`` template has changed slightly in py2app 0.3 in order
to accommodate the enhancements brought on by `distribute`_. Old ``setup.py``
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

.. _`distribute`: http://pypi.python.org/pypi/distribute/
.. _`easy_install`: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _`develop command`: http://packages.python.org/distribute/setuptools.html#development-mode
.. _`pip`: http://www.pip-installer.org/en/latest/
.. _`sudo`: http://www.sudo.ws/sudo/intro.html
