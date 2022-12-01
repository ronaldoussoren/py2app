Py2app Configuration
====================

Introduction
------------

As of py2app 2.0 the primary way to configure a build is using
configurration in ``pyproject.toml`` (as introduced in
`PEP 518  <https://peps.python.org/pep-0518/>`_).  Note that
py2app is not a build system as described in PEP 518, using
py2app as the ``build-backend`` in  the ``build-system`` table is
not supported and will result in an error.

Configuration for py2app is stored in the ``tools.py2app`` table.

A basic example of a configuration file:


.. sourcecode:: toml

   [tools.py2app.bundle.main]

   script = "main.py"
   semi-standalone = true


The configuration for bundles supports defining multiple bundles,
but for now only a single bundle is supported. The convention is
to use ``main`` as the subkey for the primary bundle.

Global options
--------------

The options can also be included in the ``bundle`` configuration described
below, and generally have a command-line equivalent as well.

============================ ================= ===========================================================
Key                          Value Type (TOML) Description
============================ ================= ===========================================================
``build-type``               string            The type of build, one of:

                                               * ``standalone`` (default): Create a bundle that can be used
                                                 on a different machine.

                                               * ``semi-standalone``: Create a bundle that embeds all resources
                                                 except the python interpreter

                                               * ``alias``: Debug builds that links to source files instead
                                                 of copying them into the bundle.

``strip``                    bool              Strip debug information and local system from MachO files
                                               included in the bundle.  Defaults to ``true``.

``deployment-target``        string            Deployment target for the output of py2app. Defaults to
                                               the deployment target of the Python interpreter.

``arch``                     string            The set of CPU architectures to include (``x86_64``,
                                               ``arm64`` or ``universal2``). Defaults to the architecture(s)
                                               of the Python interpreter.

                                               Defaults to the set of architectures of the active
                                               interpreter.

``python.optimize``          int               Optimization level for the Python interpreter. Defaults
                                               to the level for the current interpreter.

``python.verbose``           bool              Start the Python interpreter in verbose mode
                                               (default ``false``)

``python.use_pythonpath``    bool              Use the ``PYTHONPATH`` environment variable when
                                               it is set (default ``false``)


``python.use_sitepackages``  bool              Use the site-packages directory for a semi-standalone

``python.faulthandler``      bool              Enable ``faulthandler`` (default ``false``).
============================ ================= ===========================================================

Bundle configuration
--------------------

Configuration for a bundle can contain the following keys:

============================= ================= ===========================================================
Key                           Value Type (TOML) Description
============================= ================= ===========================================================
``name``                      string            (Optional) Name of the bundle (without
                                                extension). Default is same as the
                                                basename of ``script``.

``script``                    string            Path to the main script.

``plugin``                    boolean           (Optional) Set to ``true`` for plugin
                                                bundles. Default is ``false``.

``extension``                 string            File extension for the bundle (excluding
                                                the dot). Defaults to ``app`` for
                                                application bundles and ``bundle``
                                                for plugin bundles.

``include``                   array of string   Array of modules or packages to include
                                                even when they are not detected by
                                                the dependency checker.

                                                Note that packages will only include the
                                                package itself and anything found relative
                                                to the package ``__init__``.

``exclude``                   array of string   Array of modules or packages that won't
                                                be included even when detected by the
                                                dependency checker.

``full-package``              array of string   Array of packages that will be included
                                                entirely when they are part of the dependency
                                                graph.


``dylib-include``             array of string   Array of shared libraries and frameworks
                                                that will be included, even if not
                                                detected by the dependency checker.

``dylib-exclude``             array of string   Array of shared libraries and frameworks
                                                that will not be included.

``iconfile``                  string            Path for the icon file to use. Default
                                                is a generic icon.

``resources``                 see below         Description of data files to include
                                                in the bundle.

``plist``                     table             Contents for the ``Info.plist`` file,
                                                will be merged with a py2app template.

                                                For simple programs this can can be left
                                                out.

``chdir``                     bool              Change directory to the "Contents/Resources"
                                                folder. Defaults to ``true`` for application
                                                bundles and ``false`` for plugin bundles.

``argv-emulator``             bool              Fill ``sys.argv`` by waiting for open events during
                                                startup. Defaults to ``false``.

                                                This option can only be used for application bundles,
                                                and should not be used with GUI frameworks (which generally
                                                have their own mechanism for handling open events).

``argv-inject``               array of string   Values that will be appended to ``sys.argv`` during startup

``emulate-shell-environment`` bool              Emulate the environment variables from a Terminal window
                                                by running a login shell in the background and extracting
                                                environment variables. Defaults to ``false``.

``extra-scripts``             array of string   Additional script that should be included in the bundle,
                                                will be setup for command-line invocation.

``redirect-to-asl``           bool              Redirect the stdout and stderr streams to Console.app using
                                                ASL. Defaults to ``false``. Deprecated, do no use.
============================= ================= ===========================================================

For now only a single bundle is supported. In the future there will be support for multiple bundles,
including embedding bundles (e.g. an application with embedded plugins).


Code signing configuration
--------------------------

Configuration for code signing is stored in the
``tools.py2app.codesign`` table. And can be stored in
a ``codesign`` subtable for specific bundles.

This section is intentionally left blank.


Recipe configuration
--------------------

Configuration for the recipe system is stored in the
``tools.py2app.recipes`` table. And can be stored in
a ``recipes`` subtable for specific bundles.

============================ ================= ===========================================================
Key                          Value Type (TOML) Description
============================ ================= ===========================================================
``zip-unsafe``               array of string   Array of packages and modules that are not safe to include
                                               in ``site-packages.zip``. Please file an issue with py2app
                                               for distributions on PyPI that are not zip-safe.

``qt-plugins``               array of string   The Qt plugins to include in the bundle for scripts using
                                               PyQt or PySide. Defaults to an empty array.

``matplotlib-backends``      array of string   The matplotlib backends to include for scripts using
                                               this library. Defaults to all backends.
============================ ================= ===========================================================
