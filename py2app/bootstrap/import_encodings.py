def _import_encodings():
    import os
    import imp
    import encodings
    import pkgutil
    import sys
    del sys.path[:2]
    import encodings.aliases

    encodings.__path__ = pkgutil.extend_path(
            encodings.__path__,
            encodings.__name__)
    #imp.reload(encodings)

    import encodings.mac_roman
    encodings.aliases.__file__ = os.path.join(
            os.path.dirname(encodings.mac_roman.__file__),
            'aliases.py' + encodings.mac_roman.__file__[:-1])

    imp.reload(encodings.aliases)
    imp.reload(encodings)

_import_encodings()
