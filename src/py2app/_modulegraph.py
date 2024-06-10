"""
Wrapper around class:`modulegraph2.ModuleGraph` with additional
functionality useful for py2app.
"""

import importlib.resources
import io
import typing

import modulegraph2
from modulegraph2 import (
    AliasNode,
    BaseNode,
    BuiltinModule,
    ExcludedModule,
    ExtensionModule,
    FrozenModule,
    MissingModule,
    Module,
    NamespacePackage,
    Package,
)

ATTR_ZIPSAFE = "py2app.zipsafe"
ATTR_BOOTSTRAP = "py2app.bootstrap"
ATTR_IGNORE_RESOURCES = "py2app.ignore_resources"


def load_bootstrap(bootstrap: typing.Union[str, io.StringIO]) -> str:
    """
    Load a bootstrap script and return the script text
    """
    if isinstance(bootstrap, io.StringIO):
        return bootstrap.read()

    else:
        package, _, fname = bootstrap.partition(":")
        return (
            importlib.resources.files(package)
            .joinpath(fname)
            .read_text(encoding="utf-8")
        )


class ModuleGraph(modulegraph2.ModuleGraph):
    """
    Subclass of *modulegraph2.ModuleGraph* that adds some
    py2app-specific functionality.
    """

    def set_ignore_resources(self, node: BaseNode) -> None:
        """
        Mark *node* as a node whose package resources should not
        be copied into the bundle.
        """
        node.extension_attributes[ATTR_IGNORE_RESOURCES] = True

    def ignore_resources(self, node: BaseNode) -> bool:
        """
        Return true iff the package resources for *node* should
        not be copied into the bundle.
        """
        return node.extension_attributes.get(ATTR_IGNORE_RESOURCES, False)

    def add_bootstrap(
        self, node: BaseNode, bootstrap: typing.Union[str, io.StringIO]
    ) -> None:
        """
        Add a bundle bootstrap scriptlet for a particular node in the graph
        """
        bootstrap_source = load_bootstrap(bootstrap)

        # XXX: I don't particularly like this, but is needed to be idempotent while running
        #      recipes repeatedly.
        if bootstrap_source in node.extension_attributes.get(ATTR_BOOTSTRAP, []):
            return

        node.extension_attributes.setdefault(ATTR_BOOTSTRAP, []).append(
            bootstrap_source
        )

        self.add_dependencies_for_source(bootstrap_source)

    def bootstrap(self, node: BaseNode) -> typing.Optional[str]:
        """
        Return the bootstrap scriptlet for a node, or None when
        the node doesn't have a bootstrap scriptlet.
        """
        value = node.extension_attributes.get(ATTR_BOOTSTRAP, None)
        if value:
            return "\n".join(value)

        return None

    def mark_zipunsafe(self, node: BaseNode) -> None:
        """
        Mark *node* as unsafe to be executed from a zip archive
        """
        node.extension_attributes[ATTR_ZIPSAFE] = False

    def is_zipsafe(self, node: BaseNode) -> bool:
        """
        Return False if *node* cannot be executed from a zip archive,
        return True otherwise.

        For this method extension modules are assumed to be just
        like other modules, even though Python's extension loader
        cannot load extensions from a zipfile.
        """
        if not isinstance(node, (Module, Package, NamespacePackage)):
            return True

        try:
            value = node.extension_attributes[ATTR_ZIPSAFE]
        except KeyError:
            pass
        else:
            assert isinstance(value, bool)
            return value

        if isinstance(node, Module) and node.uses_dunder_file:
            return False

        elif isinstance(node, Package):
            if ATTR_ZIPSAFE in node.init_module.extension_attributes:
                if not node.init_module.extension_attributes[ATTR_ZIPSAFE]:
                    node.extension_attributes[ATTR_ZIPSAFE] = False
                    return False
            elif node.init_module.uses_dunder_file:
                node.extension_attributes[ATTR_ZIPSAFE] = False
                return False

        #
        # Package, and all modules in them, are either zipsafe or
        # note. We cannot have a package that is zipsafe but containing
        # modules or subpackages that aren't.
        #

        if "." in node.identifier:
            # The name is in package, use the root package to start
            # the scan.
            base = self.find_node(node.identifier.partition(".")[0])
        elif isinstance(node, (Package, NamespacePackage)):
            base = node
        else:
            # By default standalone modules are zipsafe
            return True

        base_identifier = f"{base.identifier}."

        # This function uses the 'py2app.zipsafe' attribute to cache
        # the zipsafe status of a package.
        try:
            value = base.extension_attributes[ATTR_ZIPSAFE]
        except KeyError:
            pass
        else:
            assert isinstance(value, bool)
            return value

        for subnode in self.iter_graph():
            if not subnode.identifier.startswith(base_identifier):
                continue

            if subnode.extension_attributes.get(ATTR_ZIPSAFE, None) is False:
                base.extension_attributes[ATTR_ZIPSAFE] = False
                return False

        base.extension_attributes[ATTR_ZIPSAFE] = True
        return True

    def collect_nodes(
        self,
    ) -> typing.Tuple[typing.List[BaseNode], typing.List[BaseNode]]:
        """
        Return 2 lists:
            1. Nodes to include in the zipfile (this includes Extensions)
            2. Nodes that should be kept outside of the zipfile
        """
        zip_nodes: typing.List[BaseNode] = []
        unzip_nodes: typing.List[BaseNode] = []

        for node in self.iter_graph():
            if isinstance(
                node,
                (BuiltinModule, FrozenModule, AliasNode, MissingModule, ExcludedModule),
            ):
                continue

            if isinstance(node, ExtensionModule) and "." not in node.identifier:
                # Toplevel extension modules are always kept outside of the zipfile
                unzip_nodes.append(node)
            elif self.is_zipsafe(node):
                zip_nodes.append(node)
            else:
                unzip_nodes.append(node)

        return zip_nodes, unzip_nodes
