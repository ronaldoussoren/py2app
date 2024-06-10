"""
Recipes related to the standard library
"""

import importlib.resources

from modulegraph2 import MissingModule, ModuleGraph, Package

from .._config import RecipeOptions
from .._modulegraph import ATTR_ZIPSAFE
from .._recipes import recipe

# References between modules in the standard
# library that should be ignored when building
# a bundle.
UNNEEDED_REFS = [
    # module, [ref, ...]
    (
        "pydoc",
        [
            "Tkinter",
            "tty",
            "BaseHTTPServer",
            "mimetools",
            "select",
            "threading",
            "ic",
            "getopt",
            "tkinter",
            "win32",
        ],
    ),
    ("multiprocessing.util", ["test", "test.support"]),
    ("pickle", ["doctest"]),
    ("heapq", ["doctest"]),
    ("pickletools", ["doctest"]),
    ("difflib", ["doctest"]),
]

# Standard library imports that won't be found (at least
# not on macOS) and shouldn't be reported on.
EXPECTED_MISSING = [
    ("importlib", ("_frozen_importlib_external",)),
    ("mimetypes", ("winreg",)),
    ("os", ("nt",)),
    ("re", ("sys.getwindowsversion",)),
    ("subprocess", ("_winapi",)),
    (
        "uuid",
        (
            "netbios",
            "win32wnet",
        ),
    ),
]


def _mods(values):
    return tuple(v[0] for v in values)


@recipe("ensure encodings are included")
def ensure_encodings(graph: ModuleGraph, options: RecipeOptions) -> None:
    # Python's unicode machinery can import encodings in the background,
    # prefer loading the entire package to avoid confusion.
    #
    # XXX: Add RecipeOptions to control which encodings get included,
    #      minimal set would be ascii and utf-8. Reason for this: the
    #      encodings package is 2.5 MB (uncompressed).
    node = graph.add_module("encodings")
    graph.import_package(node, "encodings")


@recipe("clean stdlib references", modules=_mods(UNNEEDED_REFS))
def clean_stdlib_refs(graph: ModuleGraph, options: RecipeOptions) -> None:
    for name, refs in UNNEEDED_REFS:
        node = graph.find_node(name)
        if node is None:
            continue

        for r in refs:
            try:
                graph.remove_all_edges(node, r)
            except KeyError:
                pass


@recipe("mark importlib as zipsafe", modules=["importlib"])
def mark_importlib_zipsafe(graph: ModuleGraph, options: RecipeOptions) -> None:
    # The 'importlib' implementation use '__file__' , but works
    # in a zipfile.
    node = graph.find_node("importlib")
    if node is None:
        return

    node.init_module.extension_attributes[ATTR_ZIPSAFE] = True
    node.extension_attributes[ATTR_ZIPSAFE] = True

    node = graph.find_node("importlib.resources._common")
    if node is None:
        return

    node.extension_attributes[ATTR_ZIPSAFE] = True


@recipe("mark expected missing stdlib references", modules=_mods(EXPECTED_MISSING))
def mark_expected_missing(graph: ModuleGraph, options: RecipeOptions) -> None:
    for python_package, expected_missing in EXPECTED_MISSING:
        m = graph.find_node(python_package)
        if m is None or m.filename is None:
            continue

        for _, m2 in graph.outgoing(m):
            if isinstance(m2, MissingModule) and m2.identifier in expected_missing:
                m.extension_attributes["py2app.expected_missing"] = True


def _contains_dylib(resources: importlib.resources.abc.Traversable):
    """
    Return true if *resources* contains a dylib somewhere in
    the resource tree.
    """
    if resources.is_file():
        return resources.name.endswith(".dylib")

    todo = list(resources.iterdir())
    while todo:
        current = todo.pop()
        if current.is_file():
            if current.name.endswith(".dylib"):
                return True
            continue

        for child in current.iterdir():
            todo.append(child)
    return False


@recipe("fixup for ctypes", modules=["ctypes"])
def use_prescript_for_importlib(graph: ModuleGraph, options: RecipeOptions) -> None:
    m = graph.find_node("ctypes")
    if m is None:
        return

    for _edge, using_module in graph.incoming(m):
        # using_module imports ctypes, mark those as
        # not-zipsafe when they contain a dylib resource.
        #
        # This ensures that the dylib can be found in
        # the filesystem regardless of how the module
        # locates it.

        if isinstance(using_module, Package):
            package = using_module
        elif "." in using_module.name:
            package = graph.find_node(using_module.name.rpartition(".")[0])
        else:
            # Toplevel module, cannot have package data.
            continue

        package_resources = importlib.resources.files(package.name)
        if _contains_dylib(package_resources):
            graph.mark_zipunsafe(using_module)

    graph.add_bootstrap(m, "py2app.bootstrap:setup_ctypes.py")

    m = graph.find_node("ctypes.macholib")
    if m is not None:
        graph.set_ignore_resources(m)
