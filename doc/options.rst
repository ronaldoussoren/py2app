py2app Options
==============

Options can be specified to py2app to influence the build procedure in three
different ways:

At the command line::

    $ python setup.py py2app --argv-emulation

In your ``setup.py``::

    setup(
        app=['MyApplication.py'],
        options=dict(py2app=dict(
            argv_emulation=1,
        )),
    )

In a ``setup.cfg`` file::

   [py2app]
   argv-emulation=1

Note that when translating command-line options for use in ``setup.py``, you
must replace hyphens (``-``) with underscores (``_``). ``setup.cfg`` files
may use either hyphens or underscores, but command-line options must always
use the hyphens.


Option Reference
----------------

To enumerate the options that py2app supports, use the following command::

    $ python setup.py py2app --help

Options for 'py2app' command::

  --optimize (-O)         optimization level: -O1 for "python -O", -O2 for
                          "python -OO", and -O0 to disable [default: -O0]
  --includes (-i)         comma-separated list of modules to include
  --packages (-p)         comma-separated list of packages to include
  --iconfile              Icon file to use
  --excludes (-e)         comma-separated list of modules to exclude
  --dylib-excludes (-E)   comma-separated list of frameworks or dylibs to
                          exclude
  --datamodels            xcdatamodels to be compiled and copied into
                          Resources
  --resources (-r)        comma-separated list of additional data files and
                          folders to include (not for code!)
  --frameworks (-f)       comma-separated list of additional frameworks and
                          dylibs to include
  --plist (-P)            Info.plist template file, dict, or plistlib.Plist
  --extension             Bundle extension [default:.app for app, .plugin for
                          plugin]
  --graph (-g)            output module dependency graph
  --xref (-x)             output module cross-reference as html
  --no-strip              do not strip debug and local symbols from output
  --no-chdir (-C)         do not change to the data directory
                          (Contents/Resources) [forced for plugins]
  --semi-standalone (-s)  depend on an existing installation of Python
  --alias (-A)            use an alias to current source file (for development
                          only!)
  --argv-emulation (-a)   use argv emulation [disabled for plugins].
  --argv-inject           inject some commands into the argv
  --use-pythonpath        allow PYTHONPATH to effect the interpreter's
                          environment
  --use-faulthandler      enable the faulthandler (with python 3.3 or later)
  --verbose-interpreter   Start python in verbose mode
  --bdist-base (-b)       base directory for build library (default is build)
  --dist-dir (-d)         directory to put final built distributions in
                          (default is dist)
  --site-packages         include the system and user site-packages into
                          sys.path
  --strip (-S)            strip debug and local symbols from output (on by
                          default, for compatibility)
  --prefer-ppc		  Force application to run translated on i386
                          (LSPrefersPPC=True)
  --debug-modulegraph     drop to pdb console after the module finding phase
                          is complete
  --debug-skip-macholib   skip macholib phase (app will not be standalone!)
  --emulate-shell-environment emulate the shell environment in a Terminal window
  --qt-plugins            comma-separated list of Qt plugins to include in a
                          application using PyQt4.
  --matplotlib-backends   comma-separated list of matplotlib backends to include
                          in an application using that library. The default is
                          to include all of matplotlib. Use '*' to include all
                          backends, and '-' to only include backends that are
                          explicitly imported.
  --extra-scripts         comma-separated list of additional scripts to include
                          in an application or plugin.
  --include-plugins       comma-seperated list of additional plugins to include
                          in an application
  --arch=ARCH             The architecture set to include (intel, fat, universal, ...)
                          NOTE: The ARCH should be a subset of the architectures supported
                          by the python interpreter.
