py2app Options
==============

Options can be specified to py2app to influence the build procedure in three
different ways:

At the command line::

    $ python setup.py py2app --includes=os,platform

In your ``setup.py``::

    setup(
        app=['MyApplication.py'],
        options=dict(py2app=dict(
            includes=["os", "platform"]
        )),
    )

In a ``setup.cfg`` file::

   [py2app]
   includes=os,platform

Note that when translating command-line options for use in ``setup.py``, you
must replace hyphens (``-``) with underscores (``_``). ``setup.cfg`` files
may use either hyphens or underscores, but command-line options must always
use the hyphens.

Lists of values are a comma seperated sequence of names on the command-line and
in setup.cfg, and regular python lists in setup.py (as shown in the earlier example).


Option Reference
----------------

To enumerate the options that py2app supports, use the following command::

    $ python setup.py py2app --help

Options for 'py2app' command:

.. list-table:: Options
   :widths: 15 15 20 50
   :header-rows: 1

   * - Command-line
     - Setup.py
     - Value
     - Description

   * - ``--optimize``
     - optimize
     - level (integer)
     - Specifies the optimization level for the Pytho interpreter
       level 0 to disable, level 1 for ``python -O``, and level 2
       for ``python -OO``. Defaults to the optimation level of the
       process running py2app.
  
   * - ``--includes``
     - includes
     - list of module names
     - A list of Python modules to include even if they are
       not detected by dependency checker. Packages in this list
       are ignored.
 
   * - ``--packages``
     - packages
     - list of package names
     - A list of Python packages to include even if they are
       not detected by dependency checker. The whole package will
       be included.

   * - ``--excludes``
     - excludes
     - list of module or package names
     - A list of Python modules or packages to exclude even if they are
       detected by dependency checker. 

   * - ``--matplotlib-backends``
     - matplotlib_backends  
     - List of matplotlib backend names
     - The matplotlib backends that will be included when matplotlib is
       one of the included libraries. The default is to include all of
       matplotlib. 
       
       Use '*' to include all backends, and "-" to only include backends that 
       are explicitly included.

   * - ``--qt-plugins``
     - qt_plugins
     - List of Qt plugins
     - Specifies plugins to include in an application using PyQt4.
 
   * - ``--dylib-excludes``
     - dylib_excludes
     - A list of shared libraries or frameworks
     - The specified libraries and frameworks will not be included
       in the output. 

   * - ``--frameworks``
     - frameworks
     - A list of shared libraries or frameworks
     - The specified libraries and frameworks will be included
       in the output.

   * - ``--iconfile``
     - iconfile
     - Path the the icon file
     - Specify the icon to use for the application, the ".icns" suffix
       may be left off. The default is to use a generic icon.

   * - ``--plist``
     - plist
     - Path to a plist template, or (in setup.py) a Python dictionary.
     - Specify the contents of the Info.plist. Py2app will add some information
       to the file when it is copied into the output.
   
   * - ``--datamodels``
     - datamodels
     - List of xcdatamodels
     - The specified xcdatamodel files will be compiled and included
       into the bundle Resources

   * - ``--mappingmodels``
     - mappingmodels
     - List of xcmappingmodels
     - The specified xcmappingmodel files will be compiled and included
       into the bundle Resources

   * - ``--resources``
     - resources
     - List of files and folders
     - Specifies additional files and folders to include in the bundle
       Resource. Do not use this to copy additional code.

   * - ``--extension``
     - extensionn
     - file extension, includding the dot
     - The extension to use of the output, defaults to ".app" for applications
       and ".plugin" for plugins. Commonly only used for plugins.

   * - ``--arch``
     - arch
     - "intel", "fat", "universal", "universal2", "i386", "x86_64", "ppc"
     - The (set of) architecture(s) to use for the main executable in the
       output. This should be a subset of the architectures supported by the
       python interpreter.
  
   * - ``--no-strip``
     - no_strip
     - None (use ``True`` in setup.py)
     - Don't strip debug information and local symbols from the output. Default
       is to strip.

   * - ``--semi-standalone``   
     - semi_standalone
     - None (use ``True`` in setup.py)
     - Create output that depends on an existing installation of Python, but
       does contain all code and dependencies.

   * - ``--alias``
     - alias
     - None (use ``True`` in setup.py)
     - Create output that depends on an existing installation of Python and
       uses the sources outside of the bundle.  
       
       This is only useful during development, you can update source files
       and relaunche the application without rebuilding the bundle.  
       
       **Do not use for distribution**

   * - ``--graph``
     - -
     - None 
     - Emit a ".dot" file with the module dependency graph after the build. The output 
       will be stored next to the  regular output.

   * - ``--xref``
     - xref
     - None 
     - Emit a module cross reference as HTML. The output
       will be stored next to the  regular output.

   * - ``--report-missing-from-imports``
     - -
     - None (use ``True`` in setup.py)
     - Include a list of missing names for ``from module import name`` in 
       the output at the end of the py2app run.

   * - ``--no-report-missing-conditional-import``
     - -
     - None
     - Do not include missing modules that might be conditionally imported
       in the output at the end of the py2app run.

   * - ``--use-faulthandler``
     - use_faulthandler
     - None (use ``True`` in setup.py)
     - Enable the Python faulthandler, requires Python 3.3 or later.

   * - ``--no-chdir``
     - no_chdir
     - None
     - Don't change the working directory to the bundle Resource
       directory. This option is always enabled in plugins.

   * - ``--argv-emulation``   
     -  argv_emulation
     - None (use ``True`` in setup.py)
     - Fill ``sys.argv`` during program launch. 

       The argv emulator runs a small event loop during program launch
       to intercept file-open and url-open events. The to-be-opened
       resources will be added to ``sys.argv``

       **WARNING**: Do no use this option when the program uses a
       GUI toolkit. The emulator tends to confuse GUI toolkits, and 
       most GUI toolkits have APIs to react to these events at runtime
       (for example to open a file when your program is already running).
     
       This option cannot be enabled for plugins.

   * - ``--emulate-shell-environment``
     - emulate_shell_environment
     - None (use ``True`` in setup.py)
     - Set up environment variables as if the program was launched from 
       a fresh Terminal window. Don't use this with plugins.

       By default applications inherit the environment from the application
       launcher (when double clicking the application in the Finder), which
       is does not include environment variables set in the users shell profile.
       
       Only use this when the application needs to access environment varialbes
       set in the Terminal. This option is not meant for general use.

   * - ``--use-pythonpath``
     - use_pythonpath
     - None (use ``True`` in setup.py)
     - Allow the PYTHONPATH environment varialble to affect the interpreter's
       search path. 

       This is generally not useful, PYTHONPATH is not included in the minimal
       shell environment used by the application launcher.

   * -  ``--site-packages``
     - site_packages
     - None (use ``True`` in setup.py)
     - Include the system and user site-packages in ``sys.path``

       Note that this makes the bundle less standalone, packages installed
       on a users's system may affect the bundle.


   * - ``--extra-script``
     - extra_scripts
     - List of file names for scripts
     - The mentioned scripts will be included in the ``Contents/MacOS``.
       
       For Python scripts the file in ``Contents/MacOS`` will be a binary
       that launches the script using the Python interpreter and environment
       from the bundle. 

   * - ``--argv-inject``
     - argv_inject
     - values to inject, a single string will be split using ``shlex.split``
     - The values will be inserted in to ``sys.argv`` after ``argv[0]``.

   * - ``--bdist-base``       
     - bdist_base
     - directory name
     - base directory for build library (default is build)

   * - ``--dist-dir``       
     - dist_dir
     - directory name
     - directory to put the final built distributions in (default is dist)

   * - ``--include-plugins``
     - include_plugins
     - List of plugin bundles
     - The plugin bundles will be copied into the application bundle at
       the expected location for the type of plugin

   * - ``--redirect-stdout-to-asl``
     - redirect_stdout_to_asl
     - None (use ``True`` in setup.py)
     - Forward the stdout/stderr streams to Console.app using ASL

   * - ``--force-system-tk``  
     - force_system_tk
     - None (use ``True`` in setup.py)
     - Ensures that Tkinter will be linked to the system copy 
       of Tcl and Tk. 

       This makes the bundle smaller, but the system version of Tcl/Tk
       is ancient an buggy. Don't use this option.

       **This is a legacy option that will be dropped in a future version**

   * - ``--prefer-ppc``
     - prefer_ppc
     - None (use ``True`` in setup.py)
     - Force the application to run translated on i386

       **This is a legacy option that will be dropped in a future version**

   * - ``--debug-modulegraph``
     - debug_modulegraph
     - None (use ``True`` in setup.py)
     - Drop into the pdb debugger after building the module graph

       *This is an development option*

   * - ``--debug-skip-macholib``
     - debug_skip_macholib
     - None (use ``True`` in setup.py)
     - Don't run macholib. The output will not be standalone.

       *This is an development option*

Options to specify which objects to include or exclude (the first part of the table
above) are used to finetune the behaviour of py2app and should generally not be
necessary. Please file an issue on the py2app tracker if a package on PyPI requires
one of these options, which allows me to change py2app to do the right thing 
automatically.

