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


class ModuleGraph(modulegraph2.ModuleGraph):
    """
    Subclass of *modulegraph2.ModuleGraph* that adds some
    py2app-specific functionality.
    """

    # NOTE: Anything that fits into the generic goals for
    #       modulegraph2 should be added there.

    def set_bootstrap(self, node: BaseNode, bootstrap: str) -> None:
        """
        Add a bundle bootstrap scriptlet for a particular node in the graph
        """

        # Validate the source code:
        compile(bootstrap, f"bootstrap for {node.identifier}", dont_inherit=True)

        node.extension_attributes[ATTR_BOOTSTRAP] = bootstrap

    def bootstrap(self, node: BaseNode) -> typing.Optional[str]:
        """
        Return the bootstrap scriptlet for a node, or None when
        the node doesn't have a bootstrap scriptlet.
        """
        return node.extension_attributes.get(ATTR_BOOTSTRAP, None)

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
                    return False
            elif node.init_module.uses_dunder_file:
                return False

        # Try to avoid having packages that are partially zipsafe,
        # if any node in a package is not zipsafe the entire package
        # is not.

        if "." in node.identifier:
            # The name is in package, use the root package to start
            # the scan.
            base = self.find_node(node.identifier.split(".", 1)[0])
        elif isinstance(node, (Package, NamespacePackage)):
            base = node
        else:
            # By default standalone modules are zipsafe
            return True

        base_identifier = f"{base.identifier}."

        # This function uses the 'py2app.zipsafe' attribute to cache
        # the zipsafe status of a package.
        #
        # This is safe to do because the graph will not be updated
        # by the time this function is used.
        try:
            value = base.extension_attributes[ATTR_ZIPSAFE]
        except KeyError:
            pass
        else:
            assert isinstance(value, bool)
            return value

        # XXX: The code below needs work, this does NOT find
        #      all nodes in a package, only those explicitly
        #      imported. Using "incoming" instead of "outgoing"
        #      would help, but that also includes excluded nodes.
        #
        #      Being too conservative here would not be a problem
        #      though.

        todo = [base]
        seen = set()

        while todo:
            current = todo.pop()
            if current.identifier in seen:
                continue
            seen.add(current.identifier)

            for _, subnode in self.outgoing(node):
                if not subnode.identifier.startswith(base_identifier):
                    continue

                if isinstance(subnode, Module):
                    if subnode.uses_dunder_file:
                        base.extension_attributes[ATTR_ZIPSAFE] = False
                        subnode.extension_attributes[ATTR_ZIPSAFE] = False
                        return False

                elif isinstance(subnode, Package):
                    if ATTR_ZIPSAFE in subnode.init_module.extension_attributes:
                        if not node.init_module.extension_attributes[ATTR_ZIPSAFE]:
                            base.extension_attributes[ATTR_ZIPSAFE] = False
                            subnode.extension_attributes[ATTR_ZIPSAFE] = False
                            return False

                    elif subnode.init_module.uses_dunder_file:
                        base.extension_attributes[ATTR_ZIPSAFE] = False
                        subnode.extension_attributes[ATTR_ZIPSAFE] = False
                        return False

                    todo.append(node)
                elif isinstance(subnode, NamespacePackage):
                    todo.append(subnode)

        base.extension_attributes[ATTR_ZIPSAFE] = True
        node.extension_attributes[ATTR_ZIPSAFE] = True
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
