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
import pathlib
import typing

import packaging
import packaging.specifiers
from modulegraph2 import BaseNode, PyPIDistribution, Script

from ._config import RecipeOptions
from ._modulegraph import ModuleGraph
from ._progress import Progress

_RECIPE_FUNC = typing.Callable[[ModuleGraph, RecipeOptions], None]


class ModuleGraphProxy:
    # XXX: Class name is suboptimal
    # XXX: Typing...
    #
    # XXX: This functionality should be part of ObjectGraph,
    #      e.g. add a 'changecount' attribute that's incremented
    #      by adding/removing nodes and edges.
    def __init__(self, graph: ModuleGraph) -> None:
        self.__graph = graph
        self.__updated = False

    @property
    def is_updated(self) -> bool:
        return self.__updated

    def add_module(self, module_name: str) -> BaseNode:
        node = self.__graph.find_node(module_name)
        if node is not None:
            assert isinstance(node, BaseNode)
            return node

        self.__updated = True
        return self.__graph.add_module(module_name)

    def add_script(self, script_path: pathlib.Path) -> Script:
        node = self.__graph.find_node(str(script_path))
        if node is not None:
            assert isinstance(node, Script)
            return node
        self.__updated = True
        return self.__graph.add_script(script_path)

    def import_package(self, importing_module: BaseNode, package_name: str) -> BaseNode:
        # XXX: This is not good enough, will result in false positive update
        #      value if import_package was called earlier
        node = self.__graph.find_node(package_name)
        if node is not None:
            assert isinstance(node, BaseNode)
            if node.extension_attributes.get("py2app.full_package", False):
                return node
        self.__updated = True
        node = self.__graph.import_package(importing_module, package_name)
        assert isinstance(node, BaseNode)
        node.extension_attributes["py2app.full_package"] = True
        return node

    def import_module(self, importing_module: BaseNode, module_name: str) -> BaseNode:
        node = self.__graph.find_node(module_name)
        if node is not None:
            assert isinstance(node, BaseNode)
            try:
                self.__graph.edge_data(importing_module, node)
            except KeyError:
                pass

            else:
                return node

        self.__updated = True
        return self.__graph.import_module(importing_module, module_name)

    def add_distribution(
        self, distribution: typing.Union[PyPIDistribution, str]
    ) -> typing.Union[PyPIDistribution, str]:
        # XXX: Need check if there actually is an update
        self.__updated = True
        return self.__graph.add_distribution(distribution)

    def __getattr__(self, name: str) -> typing.Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self.__graph, name)


@dataclasses.dataclass
class RecipeInfo:
    # XXX: Should there be a name here?
    name: str
    callback: _RECIPE_FUNC

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


def recipe(
    name: str,
    *,
    distribution: typing.Optional[str] = None,
    version_spec: typing.Optional[str] = None,
    modules: typing.Sequence[str] = (),
) -> typing.Callable[[_RECIPE_FUNC], _RECIPE_FUNC]:
    # XXX: Should this move to a separate module with helper functions
    #      for recipes?
    #      Other functions in such a module could help in standardizing
    #      annotations.
    def decorator(function: _RECIPE_FUNC) -> _RECIPE_FUNC:
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


def iter_recipes(graph: ModuleGraph) -> typing.Iterator[RecipeInfo]:
    """
    Yield all recipes that are relevant for the *graph*
    """

    # Collecting the distributions is fairly expensive, but must
    # be done very time this function is called because the graph
    # may have been changed between uses.
    distributions = {d.name: d.version for d in graph.distributions()}

    for recipe in RECIPE_REGISTRY:
        if recipe.distribution is not None:
            if recipe.distribution not in distributions:
                continue

            if recipe.version_spec is not None:
                if distributions[
                    recipe.distribution
                ] not in packaging.specifiers.SpecifierSet(recipe.version_spec, True):
                    continue

        if recipe.modules:
            for name in recipe.modules:
                if graph.find_node(name) is not None:
                    break

            else:
                continue

        yield recipe


def process_recipes(
    graph: ModuleGraph, options: RecipeOptions, progress: Progress
) -> None:
    """
    Run all recipes that are relevant for *graph*

    Recipes will be evaluated multiple times because
    recipes might update the graph, which might require
    other recipes to be (re)run
    """
    task_id = progress.add_task("Processing recipes", count=None)

    steps = 0
    while True:
        proxy = typing.cast(ModuleGraph, ModuleGraphProxy(graph))

        for recipe in iter_recipes(graph):
            progress.update(task_id, current=recipe.name)
            progress.step_task(task_id)
            steps += 1

            recipe.callback(proxy, options)

        if typing.cast(ModuleGraphProxy, proxy).is_updated:
            progress.info(f"Recipe {recipe.name!r} updated the dependency graph")
        else:
            break

    progress.update(task_id, count=steps, current="")
    progress.task_done(task_id)
