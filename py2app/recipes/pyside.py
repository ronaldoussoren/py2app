import pkg_resources
import glob
import os

def check(cmd, mf):
    name = 'PySide'
    m = mf.findNode(name)
    if m is None or m.filename is None:
        return None

    from PySide import QtCore
    plugin_dir = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PluginsPath)

    resources = [pkg_resources.resource_filename('py2app', 'recipes/qt.conf')]
    for item in cmd.qt_plugins:
        if '/' not in item:
            item = item + '/*'

        if '*' in item:
            for path in glob.glob(os.path.join(plugin_dir, item)):
                resources.append((os.path.dirname('qt_plugins' + path[len(plugin_dir):]), [path]))
            else:
                resources.append((os.path.dirname(os.path.join('qt_plugins', item)), os.path.join(plugin_dir, item)))

    # PySide dumps some of its shared files
    # into /usr/lib, which is a system location
    # and those files are therefore not included
    # into the app bundle by default.
    from macholib.util import NOT_SYSTEM_FILES
    NOT_SYSTEM_FILES

    import sys
    for fn in os.listdir('/usr/lib'):
        add=False
        if fn.startswith('libpyside-python'):
            add=True
        elif fn.startswith('libshiboken-python'):
            add=True
        if add:
            NOT_SYSTEM_FILES.append(os.path.join('/usr/lib', fn)) 

    return dict(resources=resources)
