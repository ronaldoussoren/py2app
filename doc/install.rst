Installation
============


Installing with pip
-------------------

To install py2app using `pip`_, or to upgrade to the latest released version
of py2app:

.. code-block:: sh

   $ pip3 install -U py2app

Setuptools support in py2app is optional, to force the installation
of `setuptools`_ install the setuptools extra:

.. code-block:: sh

   $ pip install -U 'py2app[setuptools]'

Note that `setuptools`_ is installed by default in most Python
installations and virtual environments, which means that
the default installation command will likely work even when
using the legacy setuptools interface of py2app.

Installing from source
----------------------

The preferred way to install py2app from source is to
invoke pip in the root of the py2app source directory:

.. code-block:: sh

    $ pip install .

.. _`setuptools`: http://pypi.python.org/pypi/setuptools/
.. _`pip`: http://www.pip-installer.org/en/latest/
