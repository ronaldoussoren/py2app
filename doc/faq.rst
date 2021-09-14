Frequently Asked Questions
==========================

* "Mach-O header may be too large to relocate"

  Py2app will fail with a relocation error when
  it cannot rewrite the load commands in shared
  libraries and binaries copied into the application
  or plugin bundle.

  This error can be avoided by rebuilding binaries
  with enough space in the Mach-O headers, either
  by using the linker flag "-headerpad_max_install_names"
  or by installing shared libraries in a deeply
  nested location (the path for the install root needs
  to be at least 30 characters long).

* M1 Macs and libraries not available for arm64

  A lot of libraries are not yet available as arm64 or
  universal2 libraries.

  For applications using those libraries you can 
  create an x86_64 (Intel) application instead:

  1. Create a new virtual environment and activate this

  2. Use ``arch -x86_64 python -mpip install ...`` to
     install libraries.

     The ``arch`` command is necessary here to ensure
     that pip selects variants that are compatible with
     the x86_64 architecture instead of arm64.


  3. Use ``arch -x86_64 python setup.py py2app --arch x86_64``
     to build

  This results in an application bundle where the
  launcher is an x86_64 only binary, and where included
  C extensions and libraries are compatible with that architecture
  as well.

* Using Cython with py2app

  Cython generates C extensions. Because of that the dependency
  walker in py2app cannot find import statements in ".pyx" files".

  To create working applications you have to ensure that 
  dependencies are made visible to py2app, either by adding
  import statements to a python file that is included in the 
  application, or by using the "includes" option.

  See examples/PyQt/cython_app in the repository for an 
  example of the latter.

* Dark mode support

  .. note::

     As of py2app 0.26 the stub executables are compiled with
     a modern SDK, with an automatic fallback to the older binaries
     for old builds of Tkinter.

  The stub executables from py2app were compiled on an 
  old version of macOS and therefore the system assumes
  that applications build with py2app do not support Dark Mode
  unless you're building a "Universal 2" or "Apple Silicon" 
  application.

  To enable Dark Mode support for other builds of Python you
  need to add a key to the Info.plist file. The easiest way
  to do this is using the following option in setup.py:

  .. sourcecode:: python
  
     setup(
         ...
         options=dict(
           py2app=dict(
             plist=dict(
               NSRequiresAquaSystemAppearance=False
             )
           )
         )
     )
  
