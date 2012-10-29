Dependencies
============

Note that these dependencies should automatically be satisfied by the
installation procedure and do not need to be acquired separately.

setuptools or distribute:
   `setuptools`_ and `distribute`_ provide enhancements to `distutils`_, 
   as well as the mechanisms for creating and working with `Python Eggs`_. 

   `Distribute`_ is a fork of `setuptools`_ that amongst others adds
   support for python 3. All testing of py2app is done using `distribute`_.

macholib:
    `macholib`_ reads and writes the Mach-O object file format. 
    Used by py2app to build a dependency graph of dyld and framework
    dependencies for your application, and then to copy them into your
    application and rewrite their load commands to be ``@executable_path``
    relative. The end result is that your application is going to be
    completely standalone beyond a default install of Mac OS X. You no
    longer have to worry about linking all of your dependencies statically,
    using `install_name_tool`_, etc. It's all taken care of!

modulegraph:
    `modulegraph`_ is a replacement for the Python standard library
    `modulefinder`_. Stores the module dependency tree in a graph data
    structure and allows for advanced filtering and analysis capabilities,
    such as `GraphViz`_ dot output.

altgraph:
    `altgraph`_ is a fork of `Istvan Albert`_'s graphlib, and it used
    internally by both `macholib`_ and `modulegraph`_. It contains
    several small feature and performance enhancements over the original
    graphlib.

.. _`setuptools`: http://pypi.python.org/pypi/setuptools/
.. _`distribute`: http://pypi.python.org/pypi/distribute/
.. _`distutils`: http://docs.python.org/lib/module-distutils.html
.. _`Python Eggs`: http://peak.telecommunity.com/DevCenter/PythonEggs
.. _`Python Egg`: http://peak.telecommunity.com/DevCenter/PythonEggs
.. _`macholib`: http://pypi.python.org/pypi/macholib/
.. _`altgraph`: http://pypi.python.org/pypi/altgraph/
.. _`modulegraph`: http://pypi.python.org/pypi/modulegraph/
.. _`install_name_tool`: x-man-page://1/install_name_tool
.. _`GraphViz`: http://www.research.att.com/sw/tools/graphviz/
.. _`modulefinder`: http://docs.python.org/lib/module-modulefinder.html
.. _`Istvan Albert`: http://www.personal.psu.edu/staff/i/u/iua1/
