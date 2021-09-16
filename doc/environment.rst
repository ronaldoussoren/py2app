Environment in launched applications
====================================


Environment variables added by py2app
-------------------------------------

* ``RESOURCEPATH``

  Filesystem path for the "Resources" folder inside the application bundle


System environment
------------------

When the application is launched normally (double clicking in the Finder,
using the ``open(1)`` command) the application will be launched with a minimal
shell environment, which does not pick up changes to the environment in the 
user's shell profile.

The "emulate_shell_environment" option will run a login shell in the background
to fetch exported environment varialbles and inject them into your application. 

It is also possible to inject extra variables into the environment by using
the ``LSEnvironment`` key in the Info.plist file, for example like so:

.. sourcecode:: python

   setup(
       name='BasicApp',
       app=['main.py'],
       options=dict(py2app=dict(
           plist=dict(
               LSEnvironment=dict(
                   LANG='nl_NL.latin1',
                   LC_CTYPE='nl_NL.UTF-8',
                   EXTRA_VAR='hello world',
                   KNIGHT='ni!',
               )
              )
       )),
   )

