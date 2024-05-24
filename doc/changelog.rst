Release history
===============

py2app 0.28.8
-------------

* #525: Fix breakage with setuptools 70.

* Add support for python 3.13

py2app 0.28.7
-------------

* Introduce support for Python 3.12

py2app 0.28.6
-------------

* Fix support for Python 2.7

  These are best-effort changes, I no longer have a setup where I
  can perform a good test run for Python 2.7.


py2app 0.28.5
-------------

* #476: Update black recipe

  The black recipe no longer worked with recent versions of black
  due to relying on a metadata file from the "egg" spec that's not
  included by black's current build tool.

  The recipe now scans the python code that's next to the mypyc
  compiled extension modules for dependencies and uses that to update
  the dependency graph. This should ensure that new dependencies of
  black will be automaticly detected in the future.

* Update wheel dependencies

py2app 0.28.4
-------------

* Fix incompatibility with Python 3.11

py2app 0.28.3
-------------

* #453: Fix crash in py2applet when specifying a directory to
  include in the application bundle.

py2app 0.28.2
-------------

* Fix incompatibility with recent setuptools

py2app 0.28.1
-------------

* #448: Fix typo in qt6 recipe

* #444: Fix issue where the standard output and standard error streams
  are set to non-blocking when using py2app.

  For some reason the "ibtool" command (part of Xcode) sets these streams
  to non-blocking when compiling NIB files. I've added a context manager that
  resets the non-blocking status of these streams.

* PR #446: Fix Qt5 recipe for newer versions of PyQt5

  PR by kangi.

* #447: Fix error when using ``py2applet --help``

  Bug was introduced in the fix for #414


py2app 0.28
-----------

.. note::

   This is the last version of py2app with compatibility with
   Python 2.7. Future versions will require Python 3.6 or later.

* PR #410: Fix typo in NamedTemporyFile call

  PR by MAKOMO

* #414 Workaround for autodiscovery in setuptools 61.0

  Setuptools 61.0 introduces autodiscovery of distribution
  attributes, and that broke py2app. This version introduces
  a ``setuptools.finalize_distribution_options`` entrypoint
  in py2app that will set the distributions's *name* and
  *py_modules* attributes in a way that is compatible with
  the main code of py2app when they are not yet set (before
  autodiscovery kicks in).

  In older versions of py2app buildin an app can fail in two
  ways with setuptools 61.0 or later:

  - The name of the generated application is not based on
    the script name, but some other value.

  - Calling ``python setup.py py2app`` results in an error
    mentioning ``Multiple top-level modules discovered``.


* PR #418: Add recipe for black

  PR by mrclary

* #417: Also include package dist-info for editable installs

* The qt5 and qt6 recipes used dodge logic to detect
  if the Qt library itself is inside the python package,
  resulting in duplicate copies of Qt.

* #406: Fix incompatibility with python 2.7

  py2app 0.24 accidently broke compatibility with Python 2.7, and
  this release fixes this.

  This is the last release with Python 2.7 support, the next
  release will contain package metadata that ensures it can
  only be installed on Python 3.

* #413: Find dist-info in included pythonXX.zip

  By default the ``working_set`` of pkg_resources does not contain
  distribution information from packages included in zip files, such
  as the zipped-up stdlib + site-pakckages in py2app bundles.

  Add some monkey patching to apps using ``pkg_resources`` to fix this.

* Fix hard crash in "rtree" recipe when the package contents doesn't
  match the recipe expectations.

* #408: Add definition of ``site.PREFIXES``

* #412: Fix incompatibility with setuptools 60.8.1

  The setuptools recipe did not recoginize all vendored dependencies
  in ``pkg_resources`` and that breaks app bundles that use ``pkg_resoures``.

* PR #388: Add builtin definitions for 'quit' and 'exit' in site.py

  PR by mcclary

* PR #388: Set "ENABLE_USER_SITE=False" in site.py

  PR by mcclary

* PR #396: Update pygame recipe to remove missing icon

  PR by glyph

py2app 0.27
-----------

* #377: The qt5 and qt6 recipes caused a py2app crash when
  the PyQt5 or PyQt6 is not installed.

* #401: Fix incompatibility with setuptools 60.7 and later

* #391: Drop usage of tempfile.mktemp

* #387: Add ``site.ENABLE_USER_SITE`` in the site.py file
  for applications (value is always ``False``).


py2app 0.26.1
-------------

* #374: Actually ship the "old" stub executables introduced in version 0.26


py2app 0.26
-----------

* Stub executables were recompiled on macOS 11

  This means support for light mode/dark mode should now work out of the
  box.

  The old stub executables are still used when detecting that Tkinter
  is used with an old build of Tk.

* #1: Include ".egg-info" and ".dist-info" information in the bundled application

  This fixes any python package that uses ``pkg_resources`` to look for
  specific distributions.

* ``py2app.filters.not_stdlib_filter`` now knows about Python's "venv"

* #368: Add recipe "detect_dunder_file"

  This recipe will ensure that a Python package is stored outside
  of site-packages.zip when a module in that package uses the
  ``__file__`` variable.

  This variable is most commonly used to load resources stored in
  the package (instead of the newer ``importlib.resources`` and ``pkg_resources``
  libraries).

* #339: Add recipe for pydantic

  The recipe is needed because pydantic uses Cython to compile
  all sources (including the package ``__init__``) and therefore
  hides imports from the dependency analyzer.

* #338: Add "imageio_ffmpeg" to autopackages

* PR367: Add recipes for pandas, pylsp, and zmq

* PR367: Add docutils and pylint to autopackages

  PR by Ryan Clary (mrclary on GitHub)

* #344: Invocation of codesign on the whole bundle sometimes fails

  Py2app will now try this a number of times before giving up. This
  is at best a workaround for and doesn't completely fix the problem.

* #370: py2app now works with Python 3.10

  Python 3.10 no longer exports a (private) symbol used by the py2app
  stub executable. Switched to a public API to accomplish the same task where
  available.

* #110: Add recipe for SQLAlchemy

  The recipe includes all dialects and connectors, including implicit
  dependencies, because SQLAlchemy uses ``__import__`` to load dependencies.

* #328: Add recipe for gcloud

* #195: Add ``USER_BASE``, ``getuserbase()`` and ``getusersitepackages()``  to
  py2app's version of ``site.py``.

* #184: Add recipe for 'ssl'

  This recipe is only used for Python 3.4 or later and ensures that the
  CA bundle used by Python's ssl module is included in the app bundle and OpenSSL
  is configured to look for that bundle in the application bundle.

* #371: change default error message on launch problems

  The default error message shown when the application cannot be launched is now
  slightly more useful and refers the
  `py2app debug page <https://py2app.readthedocs.io/en/latest/debugging.html>`_.

* #345, #169: Adjust qt5 and qt6 recipes for non-PyPI installations

  The qt5 and qt6 recipes now should work when the Qt installation prefix
  is outside of the PyQt package, for example when PyQt was installed through
  homebrew.

  I've tested this for PyQt5 and made the same change to the PyQt6 recipe, although
  I haven't tested that change.

py2app 0.25
-----------

* #358: Add recipe for multiprocessing

* PR363: Add recipe for platformdirs

  PR by Ryan Clary (mrclary on GitHub)

* PR353: Add recipe for sphinx

  PR by Ryan Clary (mrclary on GitHub)

* PR352: Fix for using ipython

  PR by Ryan Clary (mrclary on GitHub)

* PR351: Tweak the matplotlib recipe

  PR by Ryan Clary (mrclary on GitHub)

* PR348: Fix for checking for dead symlinks links in py2app

  PR by Oliver Cordes (ocordes on GitHub)

* #354: Fix buggy "autopackages" and "automissing" recipes

* #350: Add sentencepiece to the autopackages list

* #359: Add recipe for PyQt6

* #349: Add recipe for OpenCV (opencv-python, ``import cv2``)

* PR365: Add RTree recipe

  PR by Ryan Clary (mrclary on GitHub)

py2app 0.24
-----------

* Consolidate recipes that just include a package
  as is into a single recipe to reduce code complexity.

* Consolidate recipes that just mark imports as expected
  missing into a single recipe to reduce code complexity.

* #334: Include binary stubs for Universal 2 and arm64 binaries in the archives

  The files were in the repository, but were excluded from the source
  and wheel archives.

py2app 0.23
-----------

* #315: Stub executables have an LC_RPATH that points to the Frameworks folder

  PR by Aleksandar Topuzović (atopuzov)

* #322: Port wxPython examples to 4.0

  PR by Hamish Mcintyre-Bhatty (hamishmb)

* #314: Don't use Image.DEBUG in the PIL recipy, that attribute is not longer valid

  PR by Aleksandar Topuzović

* #320: Process "@loader_path" in load commands

  A popular pattern in C extensions with bindins to C library on PyPI is to
  copy those C libraries into the wheel and reference those using
  an "@loader_path" linker command in the C extension. Until this release
  py2app could not process those linker commands correctly.

* #298: Add recipe for pycryptodome

* #282: Add recipe for h5py

* #283: Add recipe for tensorflow

  The recipe just includes the entire package into the generated app bundle,
  I haven't checked yet if there is a way to reduce the size of this
  package (which is rather huge).


py2app 0.22
-----------

* #319: Add ad-hoc signature for application bundles

  ARM64 binaries on macOS 11 must be signed, even if it is only an ad-hoc signature.
  py2app will now add an ad-hoc code signature.

* #300: Add support for ARM64 and Universal 2 binaries

  .. note:: Support is highly experimental, these stubs have not been tested yet.

* #299: Fix build error when building with the copy of Python 3 shipped
  with Xcode.

* #281: Generated bundle doesn't work on macOS 10.9 and 10.10.

py2app 0.21
-----------

* PR 277 (Christian Clauss): Fix some Python 3 issues

* #276: Rebuilt the binary stubs on a 10.12 machine to fix launching

py2app 0.20
-----------

* Migrate to GitHub

* #274: Fix an issue in the PyQt5 recipe

* Fix issue with emulate-shell-environment option on macOS 10.15 (Catalina)

* #269: Py2app didn't work with Python 3.8

py2app 0.19
-----------

* #251: Add recipe for "botocore"

* #253: "python setup.py py2app -A" creates invalid bundle from "venv" virtual environments

* Updated recipe for PySide2 and new recipe for Shiboken2

  Patch by Alberto Sottile.

py2app 0.18
-----------

* #250: Add recipe for "six.moves", which also works when the six
  library is vendored by other packages

py2app 0.17
-----------

* #247: The new tkinter recipe didn't work properly for installations
  that do use a framework install of Tcl/Tk.

py2app 0.16
-----------

* #244: Copy the Tcl/Tk support libraries into the application bundle for
  Python builds using a classic unix install of Tcl/Tk instead of a framework
  build.

  This results in working app bundles when a Python.org installation that
  includes Tcl/Tk (such as Python 3.7).

* Don't copy numpy into application just because the application uses
  Pillow.

* Add recipe for Pyside

  Patch by Alberto Sottile

py2app 0.15
-----------

* Fixed issues for Python 3.7, in particular changes in the plistlib library
  (Issue #242, #239)

* Updated dependencies on macholib, altgraph and modulegraph

**Due to a bug in CPython 3.7.0 using -O does not work with that version of CPython**

py2app 0.14.1
-------------

* Updated dependencies

* Updated PyPI metadata

py2app 0.14
-----------

Features:

* Started using flake8 to improve coding style

Bug fixes:

* Issue #222: The fix for issue #179 broke the argv emulator

* Issue #226: Py2app could fail while reporting on possibly missing modules

* Issue #228: The python executable included in the app bundle as ``sys.exectuable`` was not executable


py2app 0.13
-----------

Bug fixes:

* Issue 185 in PyObjC's tracker: sysconfig using ``__import__`` in Python 3.6 or
  later, which confuses modulegraph.

* Pull request #17: Location of site-packages in the "--user" location has changed

  Patch by Matt Mukerjee

Features:

* (None yet)

py2app 0.12
-----------

* Pull request #15 by Armin Samii: Safer symlink and file copying

* Update recipes: a number of recipe names conflicted with toplevel
  modules imported by recipes. This causes problems on Python 2.7 (without
  absolute imports)

py2app 0.11
-----------

- Make sure the stdout/stderr streams of the main binary of the application
  are unbuffered.

  See `issue #177 in PyObjC's repository <https://github.com/ronaldoussoren/pyobjc/issues/177/on-python3-print-does-not-automatically>`_ for more information.

- Fix issue #201: py2app is not compatible with pyvenv virtualenvs

  With additional fix by Oskari Timperi.

- Fix issue #179: the stdout/stderr streams are no longer forwarded to console.app using ASL (by default),
  use "--redirect-stdout-to-asl" to enable the redirection functionality.

  Note that for unclear reasons the redirection doesn't work on OSX 10.12 at the moment.

- Fix issue #188: Troubles with lxml.isoschematron

  The package 'lxml.isoschematron' is not zip-safe and tries to load resources using the normal
  filesystem APIs, which doesn't work when the package is part of a zipfile.

- py2applet now longer uses "argv_emulation" by default, that results in too many problems.

- Issue #174: clean up the summary about missing modules by removing warnings about things that aren't modules.

  Also notes when an module is likely an alias for some other module. These changes should remove a lot
  of false postive warnings from the output of py2app.

- Fix issue #161: opengl recipe uses "file" function that isn't present on Python 3

- Add "qt5" recipe that does the right thing for the PyQt5 wheel on PyPI (tested with PyQt5 5.6)

- Add support for "@loader_path" in the link commands of C extension.

  This makes it possible to use wheels that were processed by `delocate-listdeps <https://github.com/matthew-brett/delocate>`_
  when building application bundles.

- Do not report imports that are expected to be missing

  Patch by Barry Scott.

py2app 0.10
-----------

- The recipe for virtualenv calls a modulegraph method that was made
  private in a recent release and hence no longer worked with py2app 0.9.

  Update the recipe to work around this.


py2app 0.9
----------

- issue #146, #147: The "python" binary in MyApp.app/Contents/MacOS was
  the small stub exetable from framework builds, instead of the actual
  command-line interpreter. The result is that you couldn't use
  ``sys.executable`` to start a new interpreter, which (amongst others)
  breaks multiprocessing.

- pull request #7: Add support for PyQt5 to the sip recipe. Patch by
  Mark Montague.

- pull request #4: Copying PySide plugins was broken due to bad
  indentation.

- pull request #5: py2app was broken for python versions that
  don't use _sysconfigdata.

- issue #135: Don't sleep for a second after compiling a XIB file

- issue #134: Remove target location before copying files into
  the bundle.

- issue #133: Ensure that the application's "Framework" folder
  is on the search path for ``ctypes.util.find_library``.

- issue #132: Depend on modulegraph 0.12 to avoid build errors
  when the python code contains references to compatibility modules
  that contain SyntaxErrors for the current python version.

- Explicitly report modules that cannot be found at the end of
  the run (for non-alias builds)

  Note: This is just a warning, missing modules are not necessarily
  a problem because modulegraph can detect imports for modules that
  aren't used on OSX (for example)

- Report modules that contain syntax errors at the end of
  the run (for non-alias builds)

  Note: This is just a warning, syntax errors be valid when the
  dependency tree contains modules for the other major release
  of python (e.g a compat_py2 module that contains compatibility
  code for Python 2 and contains code that isn't valid Python 3)

py2app 0.8.1
------------

- Loading scripts didn't work when --no-chdir was used

  Reported by Barry Scott in private mail.

py2app 0.8
-----------

py2app 0.8 is a feature release


- Fixed argv emulator on OSX 10.9, the way the code detected that the application
  was launched through the Finder didn't work on that OSX release.

- The launcher binary is now linked with Cocoa, that should avoid some problems
  with sandboxed applications (in particular: standard open panels don't seem
  to work properly in a sandboxed application when the main binary is not
  linked to AppKit)

- Don't copy Python's Makefile, Setup file and the like into a bundle when
  sysconfig and distutils.sysconfig don't need these files (basicly, when
  using any recent python version).

- Fix some issues with virtualenv support:

  * detection of system installs of Python didn't work properly when using
    a virtualenv. Because of this py2app did not create a "semi-standalone"
    bundle when using a virtualenv created with /usr/bin/python.

  * "semi-standalone" bundles created from a virtualenv included more files
    when they should (in particular bits of the stdlib)

- Issue #92: Add option '--force-system-tk' which ensures that the _tkinter
  extension (used by Tkinter) is linked against the Apple build of Tcl/Tk,
  even when it is linked to another framework in Python's std. library.

  This will cause a build error when tkinter is linked with a major version of
  Tcl/Tk that is not present in /System/Library/Frameworks.

- Issue #80: Add support for copying system plugins into the application
  bundle.

  Py2app now supports a new option *include_plugins*. The value of this
  is a list of paths to plugins that should be copied into the application
  bundle.

  Items in the list are either paths, or a tuple with the plugin type
  and the path::

      include_plugins=[
        "MyPlugins/MyDocument.qlgenerator",
        ("SystemConfiguration", "MyPlugins/MyConfig.plugin"),
      ]

  Py2app currently knows about the following plugin suffixes:
  ``.qlgenerator``, ``.mdimporter``, ``.xpc``, ``.service``,
  ``.prefPane``, ``.iaplugin`` and ``.action``. These plugins
  can be added without specifying the plugin type.

- Issue #83: Setup.py now refuses to install when the current
  platform is not Mac OS X.

  This makes it clear that the package is only supported on OSX and
  avoids confusing errors later on.

- Issue #39: It is now possible to have subpackages on
  in the "packages" option of py2app.

- Issue #37: Add recipe for pyEnchant

  ..note::

    The recipe only works for installations of pyEnchant
    where pyEnchant is stored in the installation (such
    as the binary eggs on PyPI), not for installations
    that either use the "PYENCHANT_LIBRARY_PATH" environment
    variable or MacPorts.

- Issue #90: Removed the 'email' recipe, but require a new enough version
  of modulegraph instead. Because of this py2app now requires modulegraph
  0.11 or later.

py2app 0.7.4
------------

- Issue #77: the stdout/stderr streams of application and plugin bundles did not
  end up in Console.app on OSX 10.8 (as they do on earlier releases of OSX). This
  is due to a change in OSX.

  With this version the application executable converts writes to the stdout
  and stderr streams to the ASL logging subsystem with the options needed to
  end up in the default view of Console.app.

  NOTE: The stdout and stderr streams of plugin bundles are not redirected, as it
  is rather bad form to change the global environment of the host application.

- The i386, x86_64 and intel stub binaries are now compiled with clang on OSX 10.8,
  instead of an older version of GCC. The other stub versions still are compiled
  on OSX 10.6.

- Issue #111: The site.py generated by py2app now contains a USER_SITE variable
  (with a default value of ``None``) because some software tries to import the
  value.

- Py2app didn't preserve timestamps for files copied into application bundles,
  and this can cause a bytecompiled file to appear older than the corresponding
  source file (for packages copied in the bundle using the 'packages' option).

  Related to issue #101

- Py2app also didn't copy file permissions for files copied into application
  bundles, which isn't a problem in general but did cause binaries to lose
  there executable permissions (as noted on Stackoverflow)

- Issue #101: Set "PYTHONDONTWRITEBYTECODE" in the environment before
  calling Py_Initialize to ensure that the interpreter won't try to
  write bytecode files (which can cause problems when using sandboxed
  applications).

- Issue #105: py2app can now create app and plugin bundles when the main script
  has an encoding other than ASCII, in particular for Python 3.

- Issue #106: Ensure that the PIL recipe works on Python 3. PIL itself isn't
  ported yet, but Pillow does work with Python 3.

- "python setup.py install" now fails unless the machine is running Mac OS X.

  I've seen a number of reports of users that try to use py2app on Windows
  or Linux to build OSX applications. That doesn't work, py2app now fails
  during installation do make this clear.

- Disabled the 'email' recipe for python 3.x as it isn't needed there.

- Issue #91: Added a recipe for `lxml <http://lxml.de/>`, needed because
  lxml performs a number of imports from an extension and those cannot
  be detected automaticly by modulegraph.

- Issue #94: The site-packages zipfile in the application bundle now contains
  zipfile entries for directories as well. This is needed to work around
  a bug in the zipimporter for Python 3.3: it won't consider 'pkg/foo.py' to be
  in namespace package 'pkg' unless there is a zipfile entry for the 'pkg'
  folder (or there is a 'pkg/__init__.py' entry).

- Issue #97: Fixes a problem with the pyside and sip recipes when the 'qt_plugins'
  option is used for 'image_plugins'.

- Issue #96: py2app should work with python 2.6 again (previous releases didn't
  work due to using the sysconfig module introduced in python 2.7)

- Issue #99: appstore requires a number of symlinks in embedded frameworks.

  (Version 0.7 already added a link Python.frameworks/Versions/Current, this
  versions also adds Python.framework/Python and Python.framework/Resources with
  the value required by the appstore upload tool).

- Py2app copied stdlib packages into the app bundle for semi-standalone builds
  when they are mentioned in the '--packages' option (either explicitly or
  by a recipe). This was unintentional, semi-standlone builds should rely on
  the external Python framework for the stdlib.

  .. note::

     Because of this bug parts of the stdlib of ``/usr/bin/python`` could be
     copied into app bundles created with py2app.

py2app 0.7.3
------------

py2app 0.7.3 is a bugfix release

- Issue #82: Remove debug print statement from py2app.util.LOADER that
  caused problems with Python 3.

- Issue #81: Py2app now fails with an error when trying to build a bundle
  for a unix-style shared library build of Python (``--enable-shared``) unless
  you are using a recent enough patchlevel of python (2.7.4, 3.2.3, 3.3.1,
  3.4.0, all of them are not released yet).

  The build failure was added to avoid a very confusing error when trying
  to start the generated application due to a bug in the way python reads
  the environment (for shared library builds on Mac OS X).

- Py2app will also give an error message when the python binary does not
  have a shared library (or framework) at all.

- Issue #87: Ignore '.git' and '.hg' directories while copying package data
  ('.svn' and 'CVS' were already ignored).

- Issue #65: the fix in 0.7 to avoid copying a symlinked library twice caused
  problems for some users because only one of the file names ended up in the
  application bundle. This release ensures that both names exist (one as a
  symbolic name to the other).

- Issue #88: Ensure that the fix for #65 won't try to create a symlink that
  points to itself. This could for example occur with homebrew, where the
  exposed lib directory contains symlinks to a cellar, while tye install_name
  does mention the "public" lib directory::

     $ ls -l /opt/homebrew/lib
     ...
     libglib-2.0.0.dylib -> ../Cellar/glib/2.32.4/lib/libglib-2.0.0.dylib
     ...

     $ otool -vL /opt/homebrew/lib/libglib-2.0.0.dylib
     /opt/homebrew/lib/libglib-2.0.0.dylib:
        /opt/homebrew/lib/libglib-2.0.0.dylib (compatibility version 3201.0.0, current version 3201.4.0)
        time stamp 1 Thu Jan  1 01:00:01 1970
     ...



py2app 0.7.2
------------

py2app 0.7.2 is a bugfix release

- Issue #75: Don't remove ``--dist-dir``, but only remove the old version
  of the objects we're trying to build (if that exists).

  This once again makes it possible to have a number of setup.py files that
  build plugins into the same target folder (such as the plugins folder
  of an application)

- Issue #78: Packages added using the ``--packages`` option didn't end up
  on ``sys.path`` for semi-standalone applications.

  Reported by Steve Strassmann

- Issue #76: Semi-standalone packages using extensions modules coudn't use
  extensions unless they also used the ``--site-packages`` option (and
  the extensions are in the site-packages directory).

  Fixes some problems with PyQt and wxWidgets when using the system installation
  of Python.

  Patch by Dan Horner.

- It is currently not possible to use a subpackage ("foo.bar") in the list
  of packages for the "packages" option. Py2app now explicitly checks for this
  and prints an error message instead of building an application that doesn't
  work.

  Issue: #39


py2app 0.7.1
------------

py2app 0.7.1 is a bugfix release

- Always include 'pkg_resources', this is needed to correctly work with
  setuptools namespace packages, the __init__.py files of those contain
  ``__import__('pkg_resources')`` and that call isn't recognized as an import
  by the bytecode scanner.

- Issue #67: py2applet didn't work with python 3 due to the use of 'raw_input'

  Reported by Andrew Barnert.

- Issue #68: the "extra-scripts" feature introduced in 0.7 couldn't copy scripts
  that aren't in the same directory as "setup.py".

  Reported by Andrew Barnert.

- For semi-standalone applications the "lib-dynload" directory inside the
  application was not on "sys.path", which resulted in launch failures
  when using an extension that is not in the stdlib.

- Issue #70: application fails to launch when script uses Windows line endings

  Reported by Luc Jean.

py2app 0.7
------------

py2app 0.7 is a bugfix release

- Issue #65: generated bundle would crash when two libraries linked to the
  same library using different names (one refering to the real name, the other
  to a symlink).

  An example if this is an application using wxWidgets when wxWidgets is installed
  using homebrew.

  Reported by "Bouke".

- Issue #13: It is now possible to add helper scripts to a bundle, for
  example for creating a GUI that starts a helper script in the background.

  This can be done by using the option "--extra-scripts", the value of which is a list
  of script files (".py" or ".pyw" files).

- Smarter matplotlib recipe, it is now possible to specify which backends should
  be included. Issue #44, reported by Adam Kovics.

  The argument to ``--matplotlib-backends`` (or 'matplotlib_backends' in setup.py)
  is a list of plugins to include. Use '-' to not include backends other than those
  found by the import statement analysis, and '*' to include all backends (without
  necessarily including all of matplotlib)

  As an example, use ``--matplotlib-backends=wxagg`` to include just the wxagg
  backend.

  Default is to include the entire matplotlib package.

- The packages included by a py2app recipe weren't processed by modulegraph and
  hence their dependencies were not always included.

- Fix virtualenv support: alias builds in a virtual environment failed to work.

  (There are still issues with semi-standalone and alias plugin bundles in
  a virtualenv environment).

- issue #18: improved PyQt and PySide support.

  Py2app now has a new option named "--qt-plugins" (or "qt_plugins" in setup.py),
  this option specify a list of plugins that should be included in the
  application bundle. The items of the list can have a number of forms:

  * "plugintype/libplugin.dylib"

    Specify one particular plugin

  * "plugintype/\*foo\*"

    Specify one or more plugins using a glob pattern

  * "plugintype"

    Include all plugins of a type, equivalent to "plugintype/\*".

  The plugins are copied into "Resources/qt_plugins" and py2app adds a "qt.conf"
  file that points to that location for plugins.

- issue #49: package data that is a zipfile is now correctly copied into
  the bundle instead of extracting the archive.

- issue #59: compile site.py to ensure that the generated bundle doesn't
  change on first run.

  This is nice to have in general, and essential when using code signing
  because the signature will break when a new file is added after signing.

  Reported by Michael McCracken.

- issue #60: recipe for "email" package was not loaded

  Reported by Chris Beaumont

- issue #46: py2app no longer warns about the Qt license. We don't warn about
  other possibly GPL licensed software either and py2app is not
  a license-enforcement tool.

  Reported by briank_in_la.

- Generated bundles always started with python optimization active
  (that is, as if running as 'python -O').

- Fix issue #53: py2app would crash if a data file happened to
  be a zipfile.

- py2app copies data files in the directory for a package into
  the application bundle. It also did this for directories that
  represent subpackages, which made it impossible to exclude
  subpackages.

- added recipe for wxPython because some subpackages of wxPython
  use ``__path__`` trickery that confuses modulegraph.

- recipes can now return a list of additional entries for the
  'includes' list.

- rewritten the recipe for matplotlib. The recipe no longer includes
  the entire package, but just the "mpl-data" directory.

  WARNING: This recipe has had limited testing.

- fix mixed indentation (tabs and spaces) in argv_emulation.py,
  which caused installation failures on python 3.x (issue #40)

- Issue #43: py2app now creates a symlink named "Current" in the
  'Versions' directory of the embedded Python framework to comply
  with a requirement for the Mac App-store.

- on some OSX releases the application receives both the
  "open application" and "open documents" Apple Events during startup,
  which broke an assumption in argv_emulation.py.

- py2app is more strict w.r.t. explictly closing files, this avoids
  ResourceWarnings for unclosed files.

- fix test issue with semi-standalone builds on Python 3.2

- added recipe for pyzmq

- Don't use the version information from Python.framework's Info.plist,
  but use ``sys.version_info``. This fixes a build problem with EPD.

- Ignore some more files when copying package data:

  - VIM swap files (``.foo.py.swp``)

  - Backup files for a number of tools: ``foo.orig`` and ``foo~``

py2app 0.6.4
------------

py2app 0.6.4 is a bugfix and minor feature release

- Issue #28: the argv emulator crashes in 64-bit mode on OSX 10.5

  Fixing this issue required yet another rewrite of the argv_emulator
  code.

- Added option '--arch=VALUE' which can be used to select the set of
  architectures for the main executable. This defaults to the set of
  architectures supported by the python interpreter and can be used to
  drop support for some architectures (for example when you're using a
  python binary that supports both 32-bit and 64-bit code and use a
  GUI library that does not yet work in 64-bit mode).

  Valid values for the argument are archectures used in the list below
  and the following groups of architectures:

  * fat:        i386, ppc

  * fat3:       i386, x86_64, ppc

  * univeral:   i386, x86_64, ppc, ppc64

  * intel:      i386, x86_64



- Issue #32: fix crash when application uses PySide

  This is partially fixed in macholib (release 1.4.3)

- The '-O' flag of py2app now defaults to the python optimization level
  when using python 2.6 or later.

- Issue #31: honor optimze flag at runtime.

  Until now an application bundle created by py2app would also run without
  the "-O" flag, even when the user specified it should. This is now fixed.

- Issue #33: py2app's application bundle launcher now clears the environment
  variable ``PYOBJC_BUNDLE_ADDRESS``, avoids a crash when using PyObjC in an
  application launched from a py2app based plugin bundle.

- py2app's bundle launcher set the environment variable ``PYOBJC_BUNDLE_ADDRESS``,
  this variable is now deprecated. Use ``PYOBJC_BUNDLE_ADDRESS<PID>`` instead
  (replace ``<PID>`` by the process ID of the current process).

- When using the system python we now explicitly add Apple's additional packages
  (like PyObjC and Twisted) to ``sys.path``.

  This fixes and issue reported by Sean Robinson: py2app used to create a non-working
  bundle when you used these packages because the packages didn't get included
  (as intented), but were not available on ``sys.path`` either.

- Fixed the recipe for sip, which in turn ensures that PyQt4 applications
  work.

  As before the SIP recipe is rather crude, it will include *all* SIP-based
  packages into your application bundle when it detects a module that uses
  SIP.

- The 'Resources' folder is no longer on the python search path,
  it contains the scripts while Python modules and packages are located
  in the site-packages directory. This change is related to issue #30.

- The folder 'Resources/Python/site-packages' is no longer on the python
  search path. This folder is not used by py2app itself, but might by
  used by custom build scripts that wrap around py2app.

- Issue #30: py2app bundles failed to launch properly when the scriptfile
  has the same name as a python package used by the application.

- Issue #15: py2app now has an option to emulate the shell environment you
  get by opening a window in the Terminal.

  Usage: ``python setup.py py2app --emulate-shell-environment``

  This option is experimental, it is far from certain that the implementation
  works on all systems.

- Issue #16: ``--argv-emulation`` now works with Python 3.x and in 64-bit
  executables.

- Issue #17: py2applet script defaults 'argv_emulation' to False when your using
  a 64-bit build of python, because that option is not supported on
  such builds.

- py2app now clears the temporary directory in 'build' and the output directory
  in 'dist' before doing anything. This avoids unwanted interactions between
  results from a previous builds and the current build.

- Issue #22: py2app will give an error when the specified version is invalid,
  instead of causing a crash in the generated executable.

- Issue #23: py2app failed to work when an .egg directory was implictly added
  to ``sys.path`` by setuptools and the "-O" option was used (for example
  ``python setup.py py2app -O2``)

- Issue #26: py2app copied the wrong executable into the application bundle
  when using virtualenv with a framework build of Python.

py2app 0.6.3
------------

py2app 0.6.3 is a bugfix release

- py2app failed to compile .xib files
  (as reported on the pythonmac-sig mail-ing list).


py2app 0.6.2
------------

py2app 0.6.2 is a bugfix release

- py2app failed to copy the iconfile into application bundle
  (reported by Russel Owen)

- py2app failed to copy resources and data files as well
  (the ``resource`` key in the py2ap options dictionary and
  the ``data_files`` argument to the setup function).

  Issue #19, reported by bryon(at)spideroak.com.

- py2app failed to build application bundles when using virtualenv
  due to assumptions about the relation between ``sys.prefix`` and
  ``sys.executable``.

  Report and fix by Erik van Zijst.

- Ensure that the 'examples' directory is included in the source
  archive

py2app 0.6.1
------------

py2app 0.6.1 is a bugfix release

Bugfixes:

- py2app failed to build the bundle when python package contained
  a zipfile with data.

  This version solves most of that problem using a rough
  workaround (the issue is fixed when the filename ends with '.zip').

- The code that recreates the stub executables when they are
  older than the source code now uses ``xcode-select`` to
  find the root of SDKs.

  This makes it possible to recreate these executables on machines
  where both Xcode 3 and Xcode 4 are installed and Xcode 3 is
  the default Xcode.

- The stub executables were regenerated using Xcode 3

  As a word of warning: Xcode 4 cannot be used to rebuild the
  stub executables, in particular not those that have support
  for the PPC architecture.

- Don't rebuild the stub executables automaticly, that's
  unsafe with Xcode 4 and could trigger accidently when
  files are installed in a different order than expected.

- Small tweaks to the testsuite to ensure that they work
  on systems with both Xcode3 and Xcode4 (Xcode3 must be
  the selected version).

- Better cleanup in the testsuite when ``setupClass`` fails.

py2app 0.6
----------

py2app 0.6 is a minor feature release


Features:

- it is now possible to specify which python distributions must
  be availble when building the bundle by using the
  "install_requires" argument of the ``setup()`` function::

     setup(

         ...
	 install_requires = [
	 	"pyobjc == 2.2"
	 ],
     )

- py2app can now package namespace packages that were installed
  using `pip <http://pypi.python.org/pypi/pip>` or the
  setuptools install option ``--single-version-externally-managed``.

- the bundle template now supports python3, based on a patch
  by Virgil Dupras.

- alias builds no longer use Carbon Aliases and therefore are
  supported with python3 as well (patch by Virgil Dupras)

- argv emulation doesn't work in python 3, this release
  will tell you abou this instead of silently failing to
  build a working bundle.

- add support for custom URLs to the argv emulation code
  (patch by Brendan Simon).

  You will have to add a "CFBundleURLTypes" key to your Info.plist to
  use this, the argv emulation code will ensure that the URL
  to open will end up in ``sys.argv``.

- ``py2app.util`` contains a number of functions that are now
  deprecated an will be removed in a future version, specifically:
  ``os_path_islink``, ``os_path_isdir``, ``path_to_zip``,
  ``get_zip_data``, ``get_mtime``,  and ``os_readlink``.

- The module ``py2app.simpleio`` no longer exists, and should never
  have been in the repository (it was part of a failed rewrite of
  the I/O layer).

Bug fixes:

- fix problem with symlinks in copied framework, as reported
  by Dan Ross.

- py2applet didn't work in python 3.x.

- The ``--alias`` option didn't work when building a plugin
  bundle (issue #10, fix by Virgil Dupras)

- Avoid copying the __pycache__ directory in python versions
  that implement PEP 3147 (Python 3.2 and later)

- App bundles with Python 3 now work when the application is
  stored in a directory with non-ASCII characters in the full
  name.

- Do not compile ``.nib`` files, it is not strictly needed and
  breaks PyObjC projects that still use the NibClassBuilder code.

- Better error messsages when trying to include a non-existing
  file as a resource.

- Don't drop into PDB when an exception occurs.

- Issue #5: Avoid a possible stack overflow in the bundle executable

- Issue #9: Work with python 3.2

- Fix build issues with python 2.5 (due to usage of too modern distutils
  command subclasses)

- The source distribution didn't include all files that needed to be
  it ever since switching to mercurial, I've added a MANIFEST.in
  file rather than relying on setuptool's autoguessing of files to include.

- Bundle template works again with semi-standalone builds (such as
  when using a system python), this rewrites the fix for issue #10
  mentioned earlier.

- Ensure py2app works correctly when the sources are located in a
  directory with non-ascii characters in its name.


py2app 0.5.2
------------

py2app 0.5.2 is a bugfix release

Bug fixes:

- Ensure that the right stub executable gets found when using
  the system python 2.5

py2app 0.5.1
------------

py2app 0.5.1 is a bugfix release

Bug fixes:

- Ensure stub executables get included in the egg files

- Fix name of the bundletemplate stub executable for 32-bit builds



py2app 0.5
----------

py2app 0.5 is a minor feature release.

Features:

- Add support for the ``--with-framework-name`` option of Python's
  configure script, that is: py2app now also works when the Python
  framework is not named 'Python.framework'.

- Add support for various build flavours of Python (32bit, 3-way, ...)

- py2app now actually works for me (ronaldoussoren@mac.com) with a
  python interpreter in a virtualenv environment.

- Experimental support for python 3

Bug fixes:

- Fix recipe for matplotlib: that recipe caused an exception with
  current versions of matplotlib and pytz.

- Use modern API's in the alias-build bootstrap code, without
  this 'py2app -A' will result in broken bundles on a 64-bit build
  of Python.
  (Patch contributed by James R Eagan)

- Try both 'import Image' and 'from PIL import Image' in the PIL
  recipe.
  (Patch contributed by Christopher Barker)

- The stub executable now works for 64-bit application bundles

- (Lowlevel) The application stub was rewritten to use
  ``dlopen`` instead of ``dyld`` APIs. This removes deprecation
  warnings during compilation.

py2app 0.4.3
------------

py2app 0.4.3 is a bugfix release

Bug fixes:

- A bad format string in build_app.py made it impossible to copy the
  Python framework into an app bundle.

py2app 0.4.2
------------

py2app 0.4.2 is a minor feature release

Features:

- When the '--strip' option is specified we now also remove '.dSYM'
  directories from the bundle.

- Remove dependency on a 'version.plist' file in the python framework

- A new recipe for `PyQt`_ 4.x. This recipe was donated by Kevin Walzer.

- A new recipe for `virtualenv`_, this allows you to use py2app from
  a virtual environment.

.. _`virtualenv`: http://pypi.python.org/pypi/virtualenv

- Adds support for converting ``.xib`` files (NIB files for
  Interface Builder 3)

- Introduces an experimental plugin API for data converters.

  A conversion plugin should be defined as an entry-point in the
  ``py2app.converter`` group::

       setup(
         ...
	 entry_points = {
		 'py2app.converter': [
		     "label          = some_module:converter_function",
		  ]
	  },
	  ...
      )

  The conversion function should be defined like this::

      from py2app.decorators import converts

      @converts('.png')
      def optimze_png(source, proposed_destionation, dryrun=0):
         # Copy 'source' to 'proposed_destination'
	 # The conversion is allowed to change the proposed
	 # destination to another name in the same directory.
         pass

.. `virtualenv`_: http://pypi.python.org/pypi/virtualenv

Buf fixes:

- This fixes an issue with copying a different version of Python over
  to an app/plugin bundle than the one used to run py2app with.


py2app 0.4.0
------------

py2app 0.4.0 is a minor feature release (and was never formally released).

Features:

- Support for CoreData mapping models (introduced in Mac OS X 10.5)

- Support for python packages that are stored in zipfiles (such as ``zip_safe``
  python eggs).

Bug fixes:

- Fix incorrect symlink target creation with an alias bundle that has included
  frameworks.

- Stuffit tends to extract archives recursively, which results in unzipped
  code archives inside py2app-created bundles. This version has a workaround
  for this "feature" for Stuffit.

- Be more carefull about passing non-constant strings as the template argumenti
  of string formatting functions (in the app and bundle templates), to avoid
  crashes under some conditions.

py2app 0.3.6
------------

py2app 0.3.6 is a minor bugfix release.

Bug fixes:

- Ensure that custom icons are copied into the output bundle

- Solve compatibility problem with some haxies and inputmanager plugins


py2app 0.3.5
------------

py2app 0.3.5 is a minor bugfix release.

Bug fixes:

- Resolve disable_linecache issue

- Fix Info.plist and Python path for plugins


py2app 0.3.4
------------

py2app 0.3.4 is a minor bugfix release.

Bug fixes:

- Fixed a typo in the py2applet script

- Removed some, but not all, compiler warnings from the bundle template
  (which is still probably broken anyway)


py2app 0.3.3
------------

py2app 0.3.3 is a minor bugfix release.

Bug Fixes:

- Fixed a typo in the argv emulation code

- Removed the unnecessary py2app.install hack (setuptools does that already)


py2app 0.3.2
------------

py2app 0.3.2 is a major bugfix release.

Functional changes:

- Massively updated documentation

- New prefer-ppc option

- New recipes: numpy, scipy, matplotlib

- Updated py2applet script to take options, provide --make-setup

Bug Fixes:

- No longer defaults to LSPrefersPPC

- Replaced stdlib usage of argvemulator to inline version for i386
  compatibility


py2app 0.3.1
------------

py2app 0.3.1 is a minor bugfix release.

Functional changes:

- New EggInstaller example

Bug Fixes:

- Now ensures that the executable is +x (when installed from egg this may not
  be the case)


py2app 0.3.0
------------

py2app 0.3.0 is a major feature enhancements release.

Functional changes:

- New --xref (-x) option similar to py2exe's that produces
  a list of modules and their interdependencies as a HTML
  file

- sys.executable now points to a regular Python interpreter
  alongside the regular executable, so spawning sub-interpreters
  should work much more reliably

- Application bootstrap now detects paths containing ":"
  and will provide a "friendly" error message instead of just
  crashing <http://python.org/sf/1507224>.

- Application bootstrap now sets PYTHONHOME instead of
  a large PYTHONPATH

- Application bootstrap rewritten in C that links to
  CoreFoundation and Cocoa dynamically as needed,
  so it doesn't imply any particular version of the runtime.

- Documentation and examples changed to use setuptools
  instead of distutils.core, which removes the need for
  the py2app import

- Refactored to use setuptools, distributed as an egg.

- macholib, bdist_mpkg, modulegraph, and altgraph are now
  separately maintained packages available on PyPI as eggs

- macholib now supports little endian architectures,
  64-bit Mach-O headers, and reading/writing of
  multiple headers per file (fat / universal binaries)


py2app 0.2.1
------------

py2app 0.2.1 is a minor bug fix release.

Bug Fixes:

- macholib.util.in_system_path understands SDKs now

- DYLD_LIBRARY_PATH searching is fixed

- Frameworks and excludes options should work again.


py2app 0.2.0
------------

py2app 0.2.0 is a minor bug fix release.

Functional changes:

- New datamodels option to support CoreData.  Compiles
  .xcdatamodel files and places them in the Resources dir
  (as .mom).

- New use-pythonpath option.  The py2app application bootstrap
  will no longer use entries from PYTHONPATH unless this option
  is used.

- py2app now persists information about the build environment
  (python version, executable, build style, etc.) in the
  Info.plist and will clean the executable before rebuilding
  if anything at all has changed.

- bdist_mpkg now builds packages with the full platform info,
  so that installing a package for one platform combination
  will not look like an upgrade to another platform combination.

Bug Fixes:

- Fixed a bug in standalone building, where a rebuild could
  cause an unlaunchable executable.

- Plugin bootstrap should compile/link correctly
  with gcc 4.

- Plugin bootstrap no longer sets PYTHONHOME and will
  restore PYTHONPATH after initialization.

- Plugin bootstrap swaps out thread state upon plug-in
  load if it is the first to initialize Python.  This
  fixes threading issues.

py2app 0.1.9
------------

py2app 0.1.9 is a minor bug fix release.

Bugs fixed:

- bdist_mpkg now builds zip files that are correctly unzipped
  by all known tools.

- The behavior of the bootstrap has changed slightly such that
  ``__file__`` should now point to your main script, rather than
  the bootstrap.  The main script has also moved to ``Resources``,
  from ``Resources/Python``, so that ``__file__`` relative resource
  paths should still work.

py2app 0.1.8
------------

py2app 0.1.8 is a major enhancements release:

Bugs fixed:

- Symlinks in included frameworks should be preserved correctly
  (fixes Tcl/Tk)

- Fixes some minor issues with alias bundles

- Removed implicit SpiderImagePlugin -> ImageTk reference in PIL
  recipe

- The ``--optimize`` option should work now

- ``weakref`` is now included by default

- ``anydbm``'s dynamic dependencies are now in the standard implies
  list

- Errors on app launch are brought to the front so the user does
  not miss them

- bdist_mpkg now compatible with pychecker (data_files had issues)

Options changed:

- deprecated ``--strip``, it is now on by default

- new ``--no-strip`` option to turn off stripping of executables

New features:

- Looks for a hacked version of the PyOpenGL __init__.py so that
  it doesn't have to include the whole package in order to get
  at the stupid version file.

- New ``loader_files`` key that a recipe can return in order to
  ensure that non-code ends up in the .zip (the pygame recipe
  uses this)

- Now scans all files in the bundle and normalizes Mach-O load
  commands, not just extensions.  This helps out when using the
  ``--package`` option, when including frameworks that have plugins,
  etc.

- An embedded Python interpreter is now included in the executable
  bundle (``sys.executable`` points to it), this currently only
  works for framework builds of Python

- New ``macho_standalone`` tool

- New ``macho_find`` tool

- Major enhancements to the way plugins are built

- bdist_mpkg now has a ``--zipdist`` option to build zip files
  from the built package

- The bdist_mpkg "Installed to:" description is now based on the
  package install root, rather than the build root

py2app 0.1.7
------------

`py2app`_ 0.1.7 is a bug fix release:

- The ``bdist_mpkg`` script will now set up sys.path properly, for setup scripts
  that require local imports.

- ``bdist_mpkg`` will now correctly accept ``ReadMe``, ``License``, ``Welcome``,
  and ``background`` files by parameter.

- ``bdist_mpkg`` can now display a custom background again (0.1.6 broke this).

- ``bdist_mpkg`` now accepts a ``build-base=`` argument, to put build files in
  an alternate location.

- ``py2app`` will now accept main scripts with a ``.pyw`` extension.

- ``py2app``'s not_stdlib_filter will now ignore a ``site-python`` directory as
  well as ``site-packages``.

- ``py2app``'s plugin bundle template no longer displays GUI dialogs by default,
  but still links to ``AppKit``.

- ``py2app`` now ensures that the directory of the main script is now added to
  ``sys.path`` when scanning modules.

- The ``py2app`` build command has been refactored such that it would be easier
  to change its behavior by subclassing.

- ``py2app`` alias bundles can now cope with editors that do atomic saves
  (write new file, swap names with existing file).

- ``macholib`` now has minimal support for fat binaries.  It still assumes big
  endian and will not make any changes to a little endian header.

- Add a warning message when using the ``install`` command rather than installing
  from a package.

- New ``simple/structured`` example that shows how you could package an
  application that is organized into several folders.

- New ``PyObjC/pbplugin`` Xcode Plug-In example.

py2app 0.1.6
------------

Since I have been slacking and the last announcement was for 0.1.4, here are the
changes for the soft-launched releases 0.1.5 and 0.1.6:

`py2app`_ 0.1.6 was a major feature enhancements release:

- ``py2applet`` and ``bdist_mpkg`` scripts have been moved to Python modules
  so that the functionality can be shared with the tools.

- Generic graph-related functionality from ``py2app`` was moved to
  ``altgraph.ObjectGraph`` and ``altgraph.GraphUtil``.

- ``bdist_mpkg`` now outputs more specific plist requirements
  (for future compatibility).

- ``py2app`` can now create plugin bundles (MH_BUNDLE) as well as executables.
  New recipe for supporting extensions built with `sip`_, such as `PyQt`_.  Note that
  due to the way that `sip`_ works, when one sip-based extension is used, *all*
  sip-based extensions are included in your application.  In practice, this means
  anything provided by `Riverbank`_, I don't think anyone else uses `sip`_ (publicly).

- New recipe for `PyOpenGL`_.  This is very naive and simply includes the whole
  thing, rather than trying to monkeypatch their brain-dead
  version acquisition routine in ``__init__``.

- Bootstrap now sets ``ARGVZERO`` and ``EXECUTABLEPATH`` environment variables,
  corresponding to the ``argv[0]`` and the ``_NSGetExecutablePath(...)`` that the
  bundle saw.  This is only really useful if you need to relaunch your own
  application.

- More correct ``dyld`` search behavior.

- Refactored ``macholib`` to use ``altgraph``, can now generate `GraphViz`_ graphs
  and more complex analysis of dependencies can be done.

- ``macholib`` was refactored to be easier to maintain, and the structure handling
  has been optimized a bit.

- The few tests that there are were refactored in `py.test`_ style.

- New `PyQt`_ example.

- New `PyOpenGL`_ example.


See also:

- http://mail.python.org/pipermail/pythonmac-sig/2004-December/012272.html

.. _`py.test`: http://codespeak.net/py/current/doc/test.html
.. _`PyOpenGL`: http://pyopengl.sourceforge.net/
.. _`Riverbank`: http://www.riverbankcomputing.co.uk/
.. _`sip`: http://www.riverbankcomputing.co.uk/sip/index.php
.. _`PyQt`: http://www.riverbankcomputing.co.uk/pyqt/index.php
.. _`docutils`: http://docutils.sf.net/
.. _`setuptools`: http://cvs.eby-sarna.com/PEAK/setuptools/

py2app 0.1.5
------------

`py2app`_ 0.1.5 is a major feature enhancements release:

- Added a ``bdist_mpkg`` distutils extension, for creating Installer
  an metapackage from any distutils script.

  - Includes PackageInstaller tool

  - bdist_mpkg script

  - setup.py enhancements to support bdist_mpkg functionality

- Added a ``PackageInstaller`` tool, a droplet that performs the same function
    as the ``bdist_mpkg`` script.

- Create a custom ``bdist_mpkg`` subclass for `py2app`_'s setup script.

- Source package now includes `PJE`_'s `setuptools`_ extension to distutils.

- Added lots of metadata to the setup script.

- ``py2app.modulegraph`` is now a top-level package, ``modulegraph``.

- ``py2app.find_modules`` is now ``modulegraph.find_modules``.

- Should now correctly handle paths (and application names) with unicode characters
  in them.

- New ``--strip`` option for ``py2app`` build command, strips all Mach-O files
  in output application bundle.

- New ``--bdist-base=`` option for ``py2app`` build command, allows an alternate
  build directory to be specified.

- New `docutils`_ recipe.
  Support for non-framework Python, such as the one provided by `DarwinPorts`_.

See also:

- http://mail.python.org/pipermail/pythonmac-sig/2004-October/011933.html

.. _`py.test`: http://codespeak.net/py/current/doc/test.html
.. _`GraphViz`: http://www.pixelglow.com/graphviz/
.. _`PyOpenGL`: http://pyopengl.sourceforge.net/
.. _`Riverbank`: http://www.riverbankcomputing.co.uk/
.. _`sip`: http://www.riverbankcomputing.co.uk/sip/index.php
.. _`PyQt`: http://www.riverbankcomputing.co.uk/pyqt/index.php
.. _`DarwinPorts`: http://darwinports.opendarwin.org/
.. _`setuptools`: http://cvs.eby-sarna.com/PEAK/setuptools/
.. _`PJE`: http://dirtSimple.org/
.. _`PyObjC`: http://pyobjc.sourceforge.net/

py2app 0.1.4
------------

`py2app`_ 0.1.4 is a minor bugfix release:

- The ``altgraph`` from 0.1.3 had a pretty nasty bug in it that prevented
  filtering from working properly, so I fixed it and bumped to 0.1.4.

py2app 0.1.3
------------

`py2app`_ 0.1.3 is a refactoring and new features release:

- ``altgraph``, my fork of Istvan Albert's `graphlib`_, is now part of the
  distribution

- ``py2app.modulegraph`` has been refactored to use ``altgraph``

- `py2app`_ can now create `GraphViz`_ DOT graphs with the ``-g`` option
  (`TinyTinyEdit example`_)

- Moved the filter stack into ``py2app.modulegraph``

- Fixed a bug that may have been in 0.1.2 where explicitly included packages
  would not be scanned by ``macholib``

- ``py2app.apptemplate`` now contains a stripped down ``site`` module as
  opposed to a ``sitecustomize``

- Alias builds are now the only ones that contain the system and user
  ``site-packages`` directory in ``sys.path``

- The ``pydoc`` recipe has been beefed up to also exclude ``BaseHTTPServer``,
  etc.

Known issues:

- Commands marked with XXX in the help are not implemented

- Includes *all* files from packages, it should be smart enough to strip
  unused .py/.pyc/.pyo files (to save space, depending on which optimization
  flag is used)

- ``macholib`` should be refactored to use ``altgraph``

- ``py2app.build_app`` and ``py2app.modulegraph`` should be refactored to
  search for dependencies on a per-application basis

.. _`graphlib`: http://www.personal.psu.edu/staff/i/u/iua1/python/graphlib/html/
.. _`TinyTinyEdit example`: http://undefined.org/~bob/TinyTinyEdit.pdf

py2app 0.1.2
------------

`py2app`_ 0.2 is primarily a bugfix release:

- The encodings package now gets included in the zip file (saves space)

- A copy of the Python interpreter is not included anymore in standalone
  builds (saves space)

- The executable bootstrap is now stripped by default (saves a little space)

- ``sys.argv`` is set correctly now, it used to point to the executable, now
  it points to the boot script.  This should enhance compatibility with some
  applications.

- Adds an "Alias" feature to modulegraph, so that ``sys.modules`` craziness
  such as ``wxPython.wx -> wx`` can be accomodated (this particular craziness
  is also now handled by default)

- A ``sys.path`` alternative may be passed to ``find_modules`` now, though
  this is not used yet

- The ``Command`` instance is now passed to recipes instead of the
  ``Distribution`` instance (though no recipes currently use either)

- The post-filtering of modules and extensions is now generalized into a
  stack and can be modified by recipes

- A `wxPython`_ example demonstrating how to package `wxGlade`_ has been
  added (this is a good example of how to write your own recipe, and how to
  deal with complex applications that mix code and data files)

- ``PyRuntimeLocations`` is now set to (only) the location of the current
  interpreter's ``Python.framework`` for alias and semi-standalone build
  modes (enhances compatibility with extensions built with an unpatched
  Makefile with Mac OS X 10.3's Python 2.3.0)

Known issues:

- Includes *all* files from packages, it should be smart enough to strip
  unused .py/.pyc/.pyo files (to save space, depending on which optimization
  flag is used).

.. _`wxGlade`: http://wxglade.sourceforge.net/

py2app 0.1.1
------------

`py2app`_ 0.1.1 is primarily a bugfix release:

- Several problems related to Mac OS X 10.2 compatibility and standalone
   building have been resolved

- Scripts that are not in the same directory as setup.py now work

- A new recipe has been added that removes the pydoc -> Tkinter dependency

- A recipe has been added for `py2app`_ itself

- a `wxPython`_ example (superdoodle) has been added.
  Demonstrates not only how easy it is (finally!) to bundle
  `wxPython`_ applications, but also how one setup.py can
  deal with both `py2exe`_ and `py2app`_.

- A new experimental tool, py2applet, has been added.
  Once you've built it (``python setup.py py2app``, of course), you should
  be able to build simple applications simply by dragging your main script
  and optionally any packages, data files, Info.plist and icon it needs.

Known issues:

- Includes *all* files from packages, it should be smart enough to strip
  unused .py/.pyc/.pyo files (to save space, depending on which
  optimization flag is used).

- The default ``PyRuntimeLocations`` can cause problems on machines that
  have a /Library/Frameworks/Python.framework installed.  Workaround is
  to set a plist that has the following key:
  ``PyRuntimeLocations=['/System/Library/Frameworks/Python.framework/Versions/2.3/Python']``
  (this will be resolved soon)


py2app 0.1
----------

(first public release)
`py2app`_ is the bundlebuilder replacement we've all been waiting
for.  It is implemented as a distutils command, similar to `py2exe`_.

.. _`wxPython`: http://www.wxpython.org/
.. _`py2app`: http://undefined.org/python/#py2app
.. _`py2exe`: http://starship.python.net/crew/theller/py2exe/
