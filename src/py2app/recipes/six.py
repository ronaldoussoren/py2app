import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo

SIX_TAB: typing.Dict[str, str] = {
    "configparser": "configparser",
    "copyreg": "copyreg",
    "cPickle": "pickle",
    "cStringIO": "io",
    "dbm_gnu": "dbm.gnu",
    "_dummy_thread": "_dummy_thread",
    "email_mime_multipart": "email.mime.multipart",
    "email_mime_nonmultipart": "email.mime.nonmultipart",
    "email_mime_text": "email.mime.text",
    "email_mime_base": "email.mime.base",
    "filterfalse": "itertools",
    "getcwd": "os",
    "getcwdb": "os",
    "http_cookiejar": "http.cookiejar",
    "http_cookies": "http.cookies",
    "html_entities": "html.entities",
    "html_parser": "html.parser",
    "http_client": "http.client",
    "BaseHTTPServer": "http.server",
    "CGIHTTPServer": "http.server",
    "SimpleHTTPServer": "http.server",
    "intern": "sys",
    "queue": "queue",
    "reduce": "functools",
    "reload_module": "importlib",
    "reprlib": "reprlib",
    "shlex_quote": "shlex",
    "socketserver": "socketserver",
    "_thread": "_thread",
    "tkinter": "tkinter",
    "tkinter_dialog": "tkinter.dialog",
    "tkinter_filedialog": "tkinter.FileDialog",
    "tkinter_scrolledtext": "tkinter.scrolledtext",
    "tkinter_simpledialog": "tkinter.simpledialog",
    "tkinter_ttk": "tkinter.ttk",
    "tkinter_tix": "tkinter.tix",
    "tkinter_constants": "tkinter.constants",
    "tkinter_dnd": "tkinter.dnd",
    "tkinter_colorchooser": "tkinter.colorchooser",
    "tkinter_commondialog": "tkinter.commondialog",
    "tkinter_tkfiledialog": "tkinter.filedialog",
    "tkinter_font": "tkinter.font",
    "tkinter_messagebox": "tkinter.messagebox",
    "tkinter_tksimpledialog": "tkinter.simpledialog",
    "urllib.robotparser": "urllib.robotparser",
    "urllib_robotparser": "urllib.robotparser",
    "UserDict": "collections",
    "UserList": "collections",
    "UserString": "collections",
    "winreg": "winreg",
    "xmlrpc_client": "xmlrpc.client",
    "xmlrpc_server": "xmlrpc.server",
    "zip_longest": "itertools",
    "urllib.parse": "urllib.parse",
    "urllib.error": "urllib.error",
    "urllib.request": "urllib.request",
    "urllib.response": "urllib.request",
}


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    found = False

    six_moves = ["six.moves"]

    # A number of libraries contain a vendored version
    # of six. Automatically detect those:
    for nm in mf.graph.node_list():
        if not isinstance(nm, str):
            continue
        if nm.endswith(".six.moves"):
            six_moves.append(nm)

    for mod in six_moves:
        m = mf.findNode(mod)
        if m is None:
            continue

        # Some users of six use:
        #
        #  import six
        #  class foo (six.moves.some_module.SomeClass): pass
        #
        # This does not refer to six.moves submodules
        # in a way that modulegraph will recognize. Therefore
        # unconditionally include everything in the
        # table...

        for submod in SIX_TAB:
            if submod.startswith("tkinter"):
                # Don't autoproces tkinter, that results
                # in significantly larger bundles
                continue

            alt = SIX_TAB[submod]

            try:
                mf.import_hook(alt, m)
                found = True
            except ImportError:
                pass

        # Look for submodules that aren't automatically
        # processed.
        for submod in SIX_TAB:
            if not submod.startswith("tkinter"):
                continue

            name = mod + "." + submod
            m = mf.findNode(name)
            if m is not None:
                alt = SIX_TAB[submod]
                mf.import_hook(alt, m)
                found = True

    if found:
        return {}

    else:
        return None
