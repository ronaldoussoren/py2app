py2applet
=========

The ``py2applet`` script can be used either to create an application
quickly in-place, or to generate a ``setup.py`` file that does the same.

In normal usage, simply run ``py2applet`` with the options you would
normally pass to the ``py2app`` command, plus the names of any scripts,
packages, icons, plist files, or data files that you want to generate
the application from.

The ``--argv-emulation`` option is assumed to be desired by default for
``py2applet`` scripts.

The first ``.py`` file is the main script. The application's name will
be derived from this main script.

The first ``.icns`` file, if any, will be used as the application's icon
(equivalent to using the ``--iconfile`` option).

Any folder given that contains an ``__init__.py`` will be wholly included as
out of the zip file (equivalent to using the ``--packages`` option).

Any other file or folder will be included in the ``Contents/Resources/``
directory of the application bundle (equivalent to the ``--resources``
option).

If ``--make-setup`` is passed as the first option to ``py2applet``, it will
generate a ``setup.py`` file that would do the above if run. This can
be used to quickly generate a ``setup.py`` for a new project, or if you
need to tweak a few complex options. The :doc:`tutorial` demonstrates this
functionality.