Tweaking your Info.plist
========================

It's often useful to make some tweaks to your Info.plist file to change how
your application behaves and interacts with Mac OS X. The most complete
reference for the keys available to you is in Apple's
`Runtime Configuration Guidelines`_.

Commonly customized keys
------------------------

Here are some commonly customized property list keys relevant to py2app
applications:

``CFBundleDocumentTypes``:
    An array of dictionaries describing document types supported by the bundle.
    Use this to associate your application with opening or editing document
    types, and/or to assign icons to document types.

``CFBundleGetInfoString``:
    The text shown by Finder's Get Info panel.

``CFBundleIdentifier``:
    The identifier string for your application (in reverse-domain syntax),
    e.g. ``"org.pythonmac.py2app"``.

``CFBundleURLTypes``:
    An array of dictionaries describing URL schemes supported by the bundle.

``LSBackgroundOnly``:
    If ``True``, the bundle will be a faceless background application. 

``LSUIElement``:
    If ``True``, the bundle will be an agent application. It will not appear
    in the Dock or Force Quit window, but still can come to the foreground
    and present a UI.

``NSServices``:
    An array of dictionaries specifying the services provided by the
    application.


Specifying customizations
-------------------------

There are three ways to specify ``Info.plist`` customizations to py2app.

You can specify an Info.plist XML file on the command-line with the
``--plist`` option, or as a string in your ``setup.py``::

    setup(
        app=['MyApplication.py'],
    options=dict(py2app=dict(
        plist='Info.plist',
    )),
    )

You may also specify the plist as a Python dict in the ``setup.py``::

    setup(
        app=['MyApplication.py'],
    options=dict(py2app=dict(
        plist=dict(
            LSPrefersPPC=True,
        ),
    )),
    )

Or you may use a hybrid approach using the standard library plistlib module::

    from plistlib import Plist
    plist = Plist.fromFile('Info.plist')
    plist.update(dict(
        LSPrefersPPC=True,
    ))
    setup(
        app=['MyApplication.py'],
    options=dict(py2app=dict(
        plist=plist,
    )),
    )


Universal Binaries
------------------

.. note:: the documentation about universal binaries is outdated!

py2app is currently fully compatible with Universal Binaries, however
it does not try and detect which architectures your application will
correctly run on.

If you are building your application with a version of Python that is not
universal, or have extensions that are not universal, then you must set
the ``LSPrefersPPC`` Info.plist key to ``True``. This will force the
application to run translated with Rosetta by default. This is necessary
because the py2app bootstrap application is universal, so Finder
will try and launch natively by default.

Alternatively, the ``--prefer-ppc`` option can be used as a shortcut to
ensure that this Info.plist key is set.

.. _`Runtime Configuration Guidelines`: http://developer.apple.com/documentation/MacOSX/Conceptual/BPRuntimeConfig/index.html
