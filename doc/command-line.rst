Invoking py2app
=================

Command-line interface
----------------------

The preferred interface for py2app is using it as a command-line tool:

.. sourcecode:: sh

   $ python3 -m py2app

This command reads configuration from a ``pyproject.toml`` file and
performs the build. The command has a number of arguments that affect
the build:

* ``--pyproject-tom FILE``

  Specify a different configuration file in the same format as
  ``pyproject.toml``. All paths in this file will be resolved
  relative to the directory containing the file.

  This option defaults to ``pyproject.toml`` in the current directory.

* ``--semi-standalone``

  Perform a semi-standalone build. This creates a bundle that
  contains all code and resources except for the Python interpreter.

* ``--alias``

  Perform an alias build. This creates a bundle that contains
  symbolic links to code and is primarily useful during development
  because it allows for a quicker edit&test cycle.

See :doc:`pyproject` for information on the structure of the pyproject
configuration file.

Legacy setuptools interface
---------------------------

Py2app before version 2.0 was an extension command for setuptools
and this interface is still supported, but is deprecated.

This interface requires using a ``setup.py`` file that contains
configuration, use ``python3 setup.py py2app`` to invoke the
setuptools command.

See :doc:`setuptools` for more information on
how to configure py2app.
