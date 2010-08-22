Implementation Details
======================

For those interested in the implementation of py2app, here's a quick
rundown of what happens.


Argument Parsing
----------------

When ``setup.py`` is run, the normal `setuptools`_ / `distutils`_
``sys.argv`` parsing takes place.


Run build command
-----------------

The ``build`` command is run to ensure that any extensions specified in the
``setup.py`` will be built prior to the ``py2app`` command. The build
directory will be added to ``sys.path`` so that ``modulegraph`` will find
the extensions built during this command.


Depdency resolution via modulegraph
-----------------------------------

The main script is compiled to Python bytecode and analyzed by modulegraph
for ``import`` bytecode. It uses this to build a dependency graph of all
involved Python modules.

The dependency graph is primed with any ``--includes``, ``--excludes``, or
``--packages`` options.


Apply recipes
-------------

All of the :doc:`recipes` will be run in order to find library-specific tweaks
necessary to build the application properly.


Apply filters
-------------

All filters specified in recipes or otherwise added to the py2app Command
object will be run to filter out the dependency graph.

The built-in filter ``not_system_filter`` will
always be run for every application built. This ensures that the contents
of your Mac OS X installation (``/usr/``, ``/System/``, excluding
``/usr/local/``) will be excluded.

If the ``--semi-standalone`` option is used (forced if a vendor Python is
being used), then the ``not_stdlib_filter`` will be automatically added to
ensure that the Python standard library is not included.


Produce graphs
--------------

If the ``--xref`` or ``--graph`` option is used, then the ``modulegraph`` is
output to HTML or `GraphViz`_ respectively. The ``.html`` or ``.dot`` file
will be in the ``dist`` folder, and will share the application's name.


Create the .app bundle
----------------------

An application bundle will be created with the name of your application.

The ``Contents/Info.plist`` will be created from the ``dict`` or filename
given in the ``plist`` option. py2app will fill in any missing keys as
necessary.

A ``__boot__.py`` script will be created in the ``Contents/Resources/`` folder
of the application bundle. This script runs any prescripts used by the
application and then your main script.

If the ``--alias`` option is being used, the build procedure is finished.

The main script of your application will be copied *as-is* to the 
``Contents/Resources/`` folder of the application bundle. If you want to
obfuscate anything (by having it as a ``.pyc`` in the zip), then you
*must not* place it in the main script!

Packages that were explicitly included with the ``packages`` option, or by
a recipe, will be placed in ``Contents/Resources/lib/python2.X/``.

A zip file containing all Python dependencies is created at
``Contents/Resources/Python/site-packages.zip``.

Extensions (which can't be included in the zip) are copied to the
``Contents/Resources/lib/python2.X/lib-dynload/`` folder.


Include Mach-O dependencies
---------------------------

`macholib`_ is used to ensure the application will run on other computers
without the need to install additional components. All Mach-O
files (executables, frameworks, bundles, extensions) used by the application
are located and copied into the application bundle.

The Mach-O load commands for these Mach-O files are then rewritten to be
``@executable_path/../Frameworks/`` relative, so that dyld knows to find
them inside the application bundle.

``Python.framework`` is special-cased here so as to only include the bare
minimum, otherwise the documentation, entire standard library, etc. would've
been included. If the ``--semi-standalone`` option or a vendor Python is used,
then the ``Python.framework`` is ignored. All other vendor files (those in
``/usr/`` or ``/System/`` excluding ``/usr/local/``) are also excluded.


Strip the result
----------------

Unless the ``--no-strip`` option is specified, all Mach-O files in the 
application bundle are stripped using the ``strip`` tool. This removes
debugging symbols to make your application smaller.


Copy Python configuration
-------------------------

This only occurs when not using a vendor Python or using the
``--semi-standalone`` option.

The Python configuration, which is used by ``distutils`` and ``pkg_resources``
is copied to ``Contents/Resources/lib/python2.X/config/``. This is needed
to acquire settings relevant to the way Python was built.

.. _`setuptools`: http://pypi.python.org/pypi/setuptools/
.. _`distutils`: http://docs.python.org/lib/module-distutils.html
.. _`GraphViz`: http://www.research.att.com/sw/tools/graphviz/
.. _`macholib`: http://pypi.python.org/pypi/macholib/