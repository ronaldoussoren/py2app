from py2app.util import imp_find_module
import os, sys, glob

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    set
except NameError:
    from sets import Set as set

try:
    basestring
except NameError:
    basestring = str


def check(cmd, mf):
    m = mf.findNode('Image') or mf.findNode('PIL.Image')
    if m is None or m.filename is None:
        return None

    if mf.findNode('PIL.Image'):
        have_PIL = True
    else:
        have_PIL = False

    plugins = set()
    visited = set()
    for folder in sys.path:
        if not isinstance(folder, basestring):
            continue

        for extra in ('', 'PIL'):
            folder = os.path.realpath(os.path.join(folder, extra))
            if (not os.path.isdir(folder)) or (folder in visited):
                continue
            for fn in os.listdir(folder):
                if not fn.endswith('ImagePlugin.py'):
                    continue

                mod, ext = os.path.splitext(fn)
                try:
                    sys.path.insert(0, folder)
                    imp_find_module(mod)
                    del sys.path[0]
                except ImportError:
                    pass
                else:
                    plugins.add(mod)
        visited.add(folder)
    s = StringIO('_recipes_pil_prescript(%r)\n' % list(plugins))
    for plugin in plugins:
        if have_PIL:
            mf.implyNodeReference(m, 'PIL.' + plugin)
        else:
            mf.implyNodeReference(m, plugin)

    mf.removeReference(m, 'FixTk')
    # Since Imaging-1.1.5, SpiderImagePlugin imports ImageTk conditionally.
    # This is not ever used unless the user is explicitly using Tk elsewhere.
    sip = mf.findNode('SpiderImagePlugin')
    if sip is not None:
        mf.removeReference(sip, 'ImageTk')

    return dict(
        prescripts = ['py2app.recipes.PIL.prescript', s],
        include = "PIL.JpegPresets", # Dodgy import from PIL.JpegPlugin in Pillow 2.0
        flatpackages = [os.path.dirname(m.filename)],
    )
