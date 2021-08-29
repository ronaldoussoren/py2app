Debugging application building
==============================

The py2app builder won't always generate a working application out of the box for
various reasons.  An incomplete build generally results in an application
that won't launch, most of the time with a generic error dialog from
py2app.

The easiest way to debug build problems is to start the application
directly in the Terminal.

Given an application "MyApp.app" you can launch the application as
follows:

.. sourcecode:: shell

   $ dist/MyApp.app/Contents/MacOS/MyApp

This will start the application as a normal shell command, with
output from the application (both stdout and stderr) shown in
the Terminal window.

Some common problems are:

* An import statement fails due to a missing module or package

  This generally happens when the dependency cannot be found
  by the source code analyzer, either due to dynamic imports
  (using ``__import__()`` or ``importlib`` to load a module),
  or due to imports in a C extension.

  In both cases use ``--includes`` or ``--packages`` to add
  the missing module to the application.

  If this is needed for a project on PyPI: Please file a bug
  on GitHub, that way we can teach py2app to do the right thing.

* C library cannot find resources

  This might happen when a C library looks for resources in
  a fixed location instead to looking relative to the library
  itself.  There are often APIs to tell the library which location
  it should use for resources.

  If this needed for a project on PyPI: Please file a bug 
  on GitHub, including the workaround, that way we can teach
  py2app to the the right thing.
