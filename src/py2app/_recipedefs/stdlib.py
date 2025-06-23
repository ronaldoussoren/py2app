"""
Recipes related to the standard library
"""

import importlib.resources
import pathlib
import sys
import textwrap
import typing

from modulegraph2 import (
    BaseNode,
    ExtensionModule,
    MissingModule,
    NamespacePackage,
    Package,
)

from .._config import RecipeOptions, Resource
from .._modulegraph import ATTR_ZIPSAFE, ModuleGraph
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
    ("copy", ("org.python.core",)),
    ("org.python.core", ("org.python",)),
    ("org.python", ("org",)),
    ("ctypes", ("nt",)),
    ("asyncio.windows_events", ("msvrt",)),
    ("pickle", ("org.python.core",)),
    ("importlib", ("_frozen_importlib_external",)),
    ("mimetypes", ("winreg",)),
    ("urllib.request", ("winreg",)),
    ("platform", ("_winreg", "vms_lib", "java", "java.lang")),
    ("java.lang", ("java",)),
    ("os", ("nt",)),
    ("ntpath", ("nt",)),
    ("getpass", ("msvcrt",)),
    ("subprocess", ("msvcrt",)),
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


def _mods(
    values: typing.Sequence[typing.Tuple[str, typing.Sequence[str]]],
) -> typing.Sequence[str]:
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

    assert isinstance(node, Package)
    node.init_module.extension_attributes[ATTR_ZIPSAFE] = True
    node.extension_attributes[ATTR_ZIPSAFE] = True

    node = graph.find_node("importlib.resources._common")
    if node is None:
        return

    assert isinstance(node, BaseNode)
    node.extension_attributes[ATTR_ZIPSAFE] = True


@recipe("mark expected missing stdlib references", modules=_mods(EXPECTED_MISSING))
def mark_expected_missing(graph: ModuleGraph, options: RecipeOptions) -> None:
    for python_package, expected_missing in EXPECTED_MISSING:
        m = graph.find_node(python_package)
        if m is None:
            continue

        assert isinstance(m, BaseNode)

        if m.filename is None:
            continue

        for _, m2 in graph.outgoing(m):
            if isinstance(m2, MissingModule) and m2.identifier in expected_missing:
                graph.set_expected_missing(m2)


def _contains_dylib(resources: importlib.resources.abc.Traversable) -> bool:
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

        package: typing.Union[Package, NamespacePackage]

        if isinstance(using_module, Package):
            package = using_module
        elif "." in using_module.name:
            found = graph.find_node(using_module.name.rpartition(".")[0])

            # Name is in package, validatet that we actually found
            # a package
            assert isinstance(found, (Package, NamespacePackage))
            package = found
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


@recipe("fixup for tkinter", modules=["_tkinter"])
def tkinter(graph: ModuleGraph, options: RecipeOptions) -> None:
    """
    Recipe to copy Tcl/Tk support libraries into the bundle.
    """
    m = graph.find_node("_tkinter")
    if m is None or not isinstance(m, ExtensionModule):
        return

    prefix = pathlib.Path(sys.base_prefix)

    paths: typing.List[pathlib.Path] = []

    lib = prefix / "lib"
    for fn in lib.iterdir():
        if not fn.is_dir():
            continue

        if fn.name.startswith("tk"):
            tk_path = fn
            paths.append(fn)

        elif fn.name.startswith("tcl"):
            tcl_path = fn
            paths.append(fn)

    if not paths:
        return

    prescript = textwrap.dedent(
        f"""\
        def _boot_tkinter():
            import os
            import sys

            resourcepath = sys.py2app_bundle_resources
            os.putenv("TCL_LIBRARY", os.path.join(resourcepath, "lib/{tcl_path.name}"))
            os.putenv("TK_LIBRARY", os.path.join(resourcepath, "lib/{tk_path.name}"))

        _boot_tkinter()
        """
    )

    graph.add_bootstrap_scriptlet(m, prescript)
    graph.add_resources(m, [Resource(destination=pathlib.Path("lib"), sources=paths)])


@recipe("fixup for ssl", modules=["ssl"])
def ssl(graph: ModuleGraph, options: RecipeOptions) -> None:
    """
    Recipe for handlign the 'ssl' module, in particular
    copying CA certificate paths (even if those are
    suboptimal

    The recipe tries to use the 'truststore' package
    when it is installed to ensure that 'ssl' uses the
    system trust store.

    The recipe warns when 'truststore' is not available,
    and when the 'ssl' module cannot access the filesystem
    based trust store (as used by 'certifi').
    """
    node = graph.find_node("ssl")
    if node is None:
        return

    ts_node = graph.find_node("truststore")
    if ts_node is None:
        try:
            import truststore  # noqa: F401
        except ImportError:
            # XXX: These warnings are printed multiple times, and should be printed
            #      through the 'progress' instance.
            # XXX: Consider adding a 'py2app.warnings' to the extension attributes
            #      of the node and print those warnings at the end of a build to
            #      get a summary at the end and have a chokepoint for deduplicating. This
            #      would also ensure that the warning is only printed when 'ssl' actually
            #      ends up in the bundle (e.g. not when a recipe drops all links to the
            #      package).
            print("WARNING: Please ensure that the 'truststore' package is installed")
            print("         to ensure that 'ssl' uses the system trust store.")

        else:
            # Automatically use 'truststore'
            graph.add_bootstrap_scriptlet(
                node,
                textwrap.dedent(
                    """\
                    import truststore

                    truststore.inject_into_ssl()
                    """
                ),
            )

            # The rest of this recipe is not necessary.
            return
    else:
        # Automatically use 'truststore' (this can result in multiple
        # calls to 'truststore.inject_into_ssl' when the application
        # also calls this function, but that is not a problem.
        graph.add_bootstrap_scriptlet(
            node,
            textwrap.dedent(
                """\
            import truststore

            truststore.inject_into_ssl()
            """
            ),
        )
        return

    import ssl

    datafiles = []
    paths = ssl.get_default_verify_paths()
    if paths.cafile is not None:
        datafiles.append(pathlib.Path(paths.cafile))
        cafile_path = str(pathlib.Path(paths.cafile).parent)
    else:
        cafile_path = None

    if paths.capath is not None:
        datafiles.append(pathlib.Path(paths.capath))
        capath_path = str(pathlib.Path(paths.capath).parent)
    else:
        capath_path = None

    if cafile_path is None and capath_path is None:
        # XXX: Should be printed to the 'progress' instance.
        print("WARNING: 'ssl' cannot validate certificates")

    prescript = textwrap.dedent(
        f"""
    def _setup_openssl():
        import os
        resourcepath = os.environ["RESOURCEPATH"]
        os.environ["{paths.openssl_cafile_env}"] = os.path.join(
            resourcepath, "openssl.ca", "{cafile_path or 'no-such-file'}")
        os.environ["{paths.openssl_capath_env}"] = os.path.join(
            resourcepath, "openssl.ca", "{capath_path or 'no-such-file'}")

    _setup_openssl()
    """
    )

    graph.add_bootstrap_scriptlet(node, prescript)
    graph.add_resources(
        node, [Resource(destination=pathlib.Path("openssl.ca"), sources=datafiles)]
    )
