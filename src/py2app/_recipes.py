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
import packaging.specifiers

from ._config import RecipeOptions
from ._modulegraph import ModuleGraph
from ._progress import Progress

_RECIPE_FUNC = typing.Callable[[ModuleGraph, RecipeOptions], None]


@dataclasses.dataclass
class RecipeInfo:
    # Name of the recipe for user reporting
    name: str

    # The actual recipe function
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
        with graph.tracked_changes() as tracker:
            for recipe in iter_recipes(graph):
                progress.update(task_id, current=recipe.name)
                progress.step_task(task_id)
                steps += 1

                recipe.callback(graph, options)

        if tracker.updated:
            progress.info(f"Recipe {recipe.name!r} updated the dependency graph")
        else:
            break

    progress.update(task_id, count=steps, current="")
    progress.task_done(task_id)
