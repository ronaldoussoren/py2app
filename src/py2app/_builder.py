import itertools

from modulegraph2 import ModuleGraph

from py2app.recipes.stdlib_refs import UNNEEDED_REFS

from ._config import BundleOptions, Py2appConfiguration


def unwanted(graph):
    # This is a hacky reproduction of the 'stdlib_refs' recipe
    for name, refs in UNNEEDED_REFS:
        node = graph.find_node(name)
        if node is None:
            continue

        for r in refs:
            try:
                graph.remove_all_edges(node, r)
            except KeyError:
                pass


class Scanner:
    def __init__(self, config: Py2appConfiguration):
        self._config = config
        self.graph = ModuleGraph()
        # self.graph.add_post_processing_hook(self._node_done)

    def process_bundle(self, bundle: BundleOptions):
        self.graph.add_excludes(bundle.py_exclude)

        for script in itertools.chain((bundle.script,), bundle.extra_scripts):
            self.graph.add_script(script)

        for module_name in bundle.py_include:
            self.graph.add_module(module_name)

        # XXX: Need a list of unnecessary imports in the stdlib, pydoc's reference
        # to tkinter is far from the only spurious import
        unwanted(self.graph)
        self.graph.report()

    def _node_done(self, graph, node):
        inc = list(graph.incoming(node))

        print(
            f"add {type(node).__name__} {node.identifier} <-- {', '.join(n[1].identifier for n in inc)}"
        )
