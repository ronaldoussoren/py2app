Recipes
=======

py2app includes a mechanism for working around package incompatibilities,
and stripping unwanted dependencies automatically. These are called recipes.

A future version of py2app will support packaging of `Python Eggs`_. Once
this is established, recipes will be obsolete since eggs contain all of the
metadata needed to build a working standalone application.


Common causes for incompatibility
---------------------------------

Some Python packages are written in such a way that they aren't compatible
with being packaged. There are two main causes of this:

- Using ``__import__`` or otherwise importing code without usage of the
  ``import`` statement.
- Requiring in-package data files


Built-in recipes
----------------

``cjkcodecs``:
    All codecs in the package are imported.

``docutils``:
    Several of its internal components are automatically imported
    (``languages``, ``parsers``, ``readers``, ``writers``,
    ``parsers.rst.directives``, ``parsers.rst.langauges``).

``matplotlib``:
    A dependency on ``pytz.zoneinfo.UTC`` is implied, and the ``matplotlib``
    package is included in its entirety out of the zip file.

``numpy``:
    The ``numpy`` package is included in its entirety out of the zip file.

``PIL``:
    Locates and includes all image plugins (Python modules that end with
    ``ImagePlugin.py``), removes unwanted dependencies on ``Tkinter``.
    
``pydoc``:
    The implicit references on the several modules are removed (``Tkinter``,
    ``tty``, ``BaseHTTPServer``, ``mimetools``, ``select``, ``threading``,
    ``ic``, ``getopt``, ``nturl2path``).

``pygame``:
    Several data files that are included in the zip file where ``pygame`` can
    find them (``freesansbold.ttf``, ``pygame_icon.tiff``,
    ``pygame_icon.icns``).

``PyOpenGL``:
    If the installed version of PyOpenGL reads a ``version`` file to determine
    its version, then the ``OpenGL`` package is included in its entirety out of
    the zip file.

``scipy``:
    The ``scipy`` and ``numpy`` packages are included in their entirety
    out of the zip file.

``sip``:
    If ``sip`` is detected, then all sip-using packages are included
    (e.g. PyQt).


Developing Recipes
------------------

py2app currently searches for recipes only in the ``py2app.recipes`` module.
A recipe is an object that implements a ``check(py2app_cmd, modulegraph)``
method.

``py2app_cmd``:
   The py2app command instance (a subclass of ``setuptools.Command``).
   See the source for ``py2app.build_app`` for reference.

``modulegraph``:
   The ``modulegraph.modulegraph.ModuleGraph`` instance.

A recipe should return either ``None`` or a ``dict`` instance.

If a recipe returns ``None`` it should not have performed any actions with
side-effects, and it may be called again zero or more times.

If a recipe returns a ``dict`` instance, it will not be called again. The
returned ``dict`` may have any of these optional string keys:

``filters``:
    A list of filter functions to be called with every module in the 
    modulegraph during flattening. If the filter returns False, the module
    and any of its dependencies will not be included in the output. This is
    similar in purpose to the ``excludes`` option, but can be any predicate
    (e.g. to exclude all modules in a given path).

``loader_files``:
    Used to include data files inside the ``site-packages.zip``. This is a
    list of 2-tuples: ``[(subdir, files), ...]``. ``subdir`` is the path
    within ``site-packages.zip`` and ``files`` is the list of files to include
    in that directory.

``packages``:
    A list of package names to be included in their entirety outside of the
    ``site-packages.zip``.

``prescripts``:
    A list of additional Python scripts to run before initializing the main
    script. This is often used to monkey-patch included modules so that they
    work in a frozen environment. The prescripts may be module names,
    file names, or file-like objects containing Python code (e.g. StringIO).
    Note that if a file-like object is used, it will not currently be scanned
    for additional dependencies.

.. _`Python Eggs`: http://peak.telecommunity.com/DevCenter/PythonEggs