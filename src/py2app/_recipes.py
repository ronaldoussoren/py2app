"""
Support for recipes

- Recipes can have guards to enable them only when
  particular distributions and/or modules are present
  in the graph

- Some of the current recipes are completely data-driven,
  convert those to a basic driver plus a data file

- All recipes for PyPI packages must have a guard for
  that package (if only to avoid problems when two
  PyPI packages define the same name).

- Non-goal (for now) is making it easy/possible to maintain
  recipes out of tree.
"""

import dataclasses
import typing

import packaging
from modulegraph2 import ModuleGraph

from ._config import RecipeOptions
from ._progress import Progress


class ModuleGraphProxy:
    # XXX: Class name is suboptimal
    # XXX: Typing...
    def __init__(self, graph):
        self.__graph = graph
        self.__updated = False

    @property
    def is_updated(self):
        return self.__updated

    def add_module(self, module_name):
        node = self.__graph.find_node(module_name)
        if node is not None:
            return node

        self.__updated = True
        return self.__graph.add_module(module_name)

    def add_script(self, script_path):
        node = self.__graph.find_node(script_path)
        if node is not None:
            return node
        self.__updated = True
        return self.__graph.add_script(script_path)

    def import_package(self, importing_module, package_name):
        # XXX: This is not good enough, will result in false positive update
        #      value if import_package was called earlier
        node = self.__graph.find_node(package_name)
        if node is not None:
            if node.extension_attributes.get("py2app.full_package", False):
                return node
        self.__updated = True
        node = self.__graph.import_package(importing_module, package_name)
        node.extension_attributes["py2app.full_package"] = True
        return node

    def import_module(self, importing_module, module_name):
        node = self.__graph.find_node(module_name)
        if node is not None:
            try:
                self.__graph.edge_data(importing_module, node)
            except KeyError:
                pass

            else:
                return node

        self.__updated = True
        return self.__graph.import_module(importing_module, module_name)

    def add_distribution(self, distribution):
        # XXX: Need check if there actually is an update
        self.__updated = True
        return self.__graph.add_distribution(distribution)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self.__graph, name)


@dataclasses.dataclass
class RecipeInfo:
    # XXX: Should there be a name here?
    name: str
    callback: typing.Callable[[ModuleGraph, RecipeOptions], None]

    # Only trigger when "distribution" is in the graph
    distribution: typing.Optional[str] = None

    # If 'distribution' is not None, the version spec
    # specifies the versions of the distribution that
    # trigger this recipe
    version_spec: typing.Optional[str] = None

    # And finally: an optional list of modules that
    # should be reachable for the recipe to trigger.
    modules: typing.Sequence[str] = ()


RECIPE_REGISTRY = []


def recipe(name, *, distribution=None, version_spec=None, modules=()):
    # XXX: Should this move to a separate module with helper functions
    #      for recipes?
    #      Other functions in such a module could help in standardizing
    #      annotations.
    def decorator(function):
        RECIPE_REGISTRY.append(
            RecipeInfo(
                name=name,
                distribution=distribution,
                version_spec=version_spec,
                modules=list(modules),
                callback=function,
            )
        )
        return function

    return decorator


def iter_recipes(graph: ModuleGraph):
    """
    Yield all recipes that are relevant for the *graph*
    """
    # XXX: This is fairly expensive,
    distributions = {d.name: d.version for d in graph.distributions()}

    for recipe in RECIPE_REGISTRY:
        if recipe.distribution is not None:
            if recipe.distribution not in distributions:
                continue

            if recipe.version_spec is not None:
                if distributions[recipe.distribution] not in packaging.VersionSpec(
                    recipe.version_spec, True
                ):
                    continue

        if recipe.modules:
            for name in recipe.modules:
                if graph.find_node(name) is not None:
                    break

            else:
                continue

        yield recipe


def process_recipes(graph: ModuleGraph, options: RecipeOptions, progress: Progress):
    """
    Run all recipes that are relevant for *graph*

    Recipes will be evaluated multiple times because
    recipes might update the graph, which might require
    other recipes to be (re)run
    """
    # XXX: How to cleanly determine if the graph has
    #      been updated?
    # XXX: Stuff should be attached to graph nodes instead
    #      of updating other state because recipes might
    #      make nodes unreachable, making state updates
    #      invalid.

    task_id = progress.add_task("Processing recipes", count=None)

    steps = 0
    while True:
        proxy = typing.cast(ModuleGraph, ModuleGraphProxy(graph))

        for recipe in iter_recipes(graph):
            progress.update(task_id, current=recipe.name)
            progress.step_task(task_id)
            steps += 1

            recipe.callback(proxy, options)

        if proxy.is_updated:
            progress.info(f"Recipe {recipe.name!r} updated the dependency graph")
        else:
            break

    progress.update(task_id, total=steps, current="")
