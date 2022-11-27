"""
Representation of the py2app configuration.

XXX: It should be possible to simplify this code
     a lot.
"""

import pathlib
import re
import sys
import sysconfig
import typing

T = typing.TypeVar("T")

_, _DEFAULT_TARGET, _DEFAULT_ARCH = sysconfig.get_platform().split("-")


class _NoDefault:
    __slots__ = ()


NO_DEFAULT = _NoDefault()


class PropertyHolder(typing.Protocol):
    _local: typing.Dict[str, typing.Any]


class InheritedPropertyHolder(typing.Protocol):
    _local: typing.Dict[str, typing.Any]
    _global: typing.Dict[str, typing.Any]


class inherited(typing.Generic[T]):
    __slots__ = ("_key", "_parent_attr")

    def __init__(self, key: str, parent_attr: str):
        self._key = key
        self._parent_attr = parent_attr

    def __get__(self, instance: InheritedPropertyHolder, owner: type) -> T:
        if self._key in instance._local:
            return typing.cast(T, instance._local[self._key])
        try:
            return typing.cast(T, getattr(instance._global, self._parent_attr))
        except KeyError:
            raise AttributeError(self._key) from None


class local(typing.Generic[T]):
    __slots__ = ("_key", "_default")

    def __init__(self, key: str, default: typing.Union[T, _NoDefault] = NO_DEFAULT):
        self._key = key
        self._default = default

    def __get__(self, instance: PropertyHolder, owner: type) -> T:
        try:
            return typing.cast(T, instance._local[self._key])
        except KeyError:
            if self._default is NO_DEFAULT:
                raise AttributeError(self._key) from None
            assert not isinstance(self._default, _NoDefault)
            return self._default


class BundleOptions:
    def __init__(self, global_options, local_options):
        self._global = global_options
        self._local = local_options

    macho_strip = inherited[bool]("strip", "macho_strip")
    macho_arch = inherited[bool]("arch", "macho_arch")
    deployment_target = inherited[str]("deployment-target", "deployment_target")
    python_optimize = inherited[int]("python.optimize", "python_optimize")
    python_verbose = inherited[bool]("python.verbose", "python_verbose")
    python_use_pythonpath = inherited[bool](
        "python.use_pythonpath", "python_use_pythonpath"
    )
    python_use_sitepackages = inherited[bool](
        "python.use_sitepackages", "python_use_sitepackages"
    )
    python_use_faulthandler = inherited[bool](
        "python.faulthandler", "python_use_faulthandler"
    )

    @property
    def name(self) -> str:
        if "name" in self._local:
            return self._local["name"]

        return self.script.stem

    script = local[pathlib.Path]("script")
    plugin = local[bool]("plugin", False)
    extension = local[str]("extension")  # Default depends on "plugin"
    iconfile = local[typing.Optional[pathlib.Path]]("iconfile", None)
    resources = local[typing.Any]("resources", ())
    plist = local[dict]("plist", {})
    extra_scripts = local[typing.Sequence[pathlib.Path]]("extra-scripts", ())

    py_include = local[typing.Sequence[str]]("include", ())
    py_exclude = local[typing.Sequence[str]]("exclude", ())
    macho_include = local[typing.Sequence[str]]("dylib-include", ())  # XXX: Path?
    macho_exclude = local[typing.Sequence[str]]("dylib-exclude", ())  # XXX: Path?

    chdir = local[bool]("chdir", True)  # Default depends on "plugin"
    argv_emulator = local[bool]("argv-emulator", False)
    argv_inject = local[typing.Sequence[str]]("argv-inject", ())
    emulate_shell_environment = local[bool]("emulate-shell-environment", False)
    redirect_to_asl = local[bool]("redirect-to-asl", False)

    def __repr__(self):
        result = []
        result.append("<BundleOptions \n")
        result.append(f"  name = {self.name!r}\n")
        result.append(f"  script = {self.script!r}\n")
        result.append(f"  plugin = {self.plugin!r}\n")
        result.append(f"  extension = {self.extension!r}\n")
        result.append(f"  iconfile = {self.iconfile!r}\n")
        result.append(f"  resources = {self.resources!r}\n")
        result.append(f"  plist = {self.plist!r}\n")
        result.append(f"  extra_scripts = {self.extra_scripts!r}\n")
        result.append(f"  py_include = {self.py_include!r}\n")
        result.append(f"  py_exclude = {self.py_exclude!r}\n")
        result.append(f"  macho_include = {self.macho_include!r}\n")
        result.append(f"  macho_exclude = {self.macho_exclude!r}\n")
        result.append(f"  chdir = {self.chdir!r}\n")
        result.append(f"  argv_emulator = {self.argv_emulator!r}\n")
        result.append(f"  argv_inject = {self.argv_inject!r}\n")
        result.append(
            f"  emulate_shell_environment = {self.emulate_shell_environment!r}\n"
        )
        result.append(f"  redirect_to_asl = {self.redirect_to_asl!r}\n")
        result.append("\n")
        result.append(f"  macho_strip = {self.macho_strip!r}\n")
        result.append(f"  macho_arch = {self.macho_arch!r}\n")
        result.append(f"  deployment_target = {self.deployment_target!r}\n")
        result.append(f"  python_optimize = {self.python_optimize!r}\n")
        result.append(f"  python_verbose = {self.python_verbose!r}\n")
        result.append(f"  python_use_pythonpath = {self.python_use_pythonpath!r}\n")
        result.append(f"  python_use_sitepackages = {self.python_use_sitepackages!r}\n")
        result.append(f"  python_use_faulthandler = {self.python_use_faulthandler!r}\n")
        result.append(">")
        return "".join(result)


class RecipeOptions:
    def __init__(self, options):
        self._local = options

    zip_unsafe = local[typing.Sequence[str]]("zip-unsafe", ())
    qt_plugins = local[typing.Optional[typing.Sequence[str]]]("qt-plugins", None)
    matplotlib_plugins = local[typing.Optional[typing.Sequence[str]]](
        "matplotlib-plugins", None
    )

    def __repr__(self):
        result = []
        result.append("<RecipeOptions \n")
        result.append(f"  zip_unsafe = {self.zip_unsafe!r}\n")
        result.append(f"  qt_plugins = {self.qt_plugins!r}\n")
        result.append(f"  matplotlib_plugins = {self.matplotlib_plugins!r}\n")

        result.append(">")
        return "".join(result)


class Py2appConfiguration:
    def __init__(self, bundles, global_options, recipe_options):
        self._local = global_options
        self.bundles = bundles
        self.recipe = recipe_options

        for bundle in bundles:
            bundle._global = self._local

    deployment_target = local[str]("deployment-target", _DEFAULT_TARGET)
    macho_strip = local[bool]("strip", True)
    macho_arch = local[str]("arch", _DEFAULT_ARCH)
    python_optimize = local[int]("python.optimize", sys.flags.optimize)
    python_verbose = local[bool]("python.verbose", bool(sys.flags.verbose))
    python_use_pythonpath = local[bool]("python.use_pythonpath", False)
    python_use_sitepackages = local[bool]("python.use_sitepackages", False)
    python_use_faulthandler = local[bool]("python.faulthandler", False)

    def __repr__(self):
        result = []
        result.append("<Py2appConfiguration \n")
        result.append(f"  deployment_target = {self.deployment_target!r}\n")
        result.append(f"  macho_strip = {self.macho_strip!r}\n")
        result.append(f"  macho_arch = {self.macho_arch!r}\n")
        result.append(f"  python_optimize = {self.python_optimize!r}\n")
        result.append(f"  python_verbose = {self.python_verbose!r}\n")
        result.append(f"  python_use_pythonpath = {self.python_use_pythonpath!r}\n")
        result.append(f"  python_use_sitepackages = {self.python_use_sitepackages!r}\n")
        result.append(f"  python_use_faulthandler = {self.python_use_faulthandler!r}\n")
        result.append("\n")
        recipe = repr(self.recipe)
        lines = recipe.splitlines()
        result.append(f"  recipes = {lines[0]}\n")
        for cur in lines[1:]:
            result.append(f"  {cur}\n")

        result.append("\n")
        result.append("  bundles = [\n")
        for entry in self.bundles:
            for cur in repr(entry).splitlines()[:-1]:
                result.append(f"    {cur}\n")
            result.append("    >,\n")
        result.append("  ]\n")

        result.append(">")
        return "".join(result)


def parse_pyproject(file_contents):
    try:
        config = file_contents["tools"]["py2app"]
    except KeyError:
        raise ValueError("TOML doesn't contain a 'tools.py2app' key") from None

    global_options = {}
    recipe_options = {}
    bundles = []

    result = Py2appConfiguration(bundles, global_options, RecipeOptions(recipe_options))
    for key, value in config.items():
        if key in {"bundle", "recipe"}:
            continue
        elif key == "recipe":
            if not isinstance(config["recipe"], dict):
                raise ValueError("'recipe' is not a dictionary")
            for key, value in config["recipe"].items():
                if key in {"zip-unsafe", "qt-plugins", "matplotlib-plugins"}:
                    if not isinstance(value, list) or not all(
                        isinstance(v, str) for v in value
                    ):
                        raise ValueError(f"Invalid value for 'recipe.{key}'")
                    recipe_options[key] = value
                else:
                    raise ValueError("Invalid key 'recipe.{key}")

        elif key == "strip":
            if not isinstance(value, bool):
                raise ValueError("'strip' is not a boolean")
            global_options["macho_strip"] = value
        elif key == "arch":
            if value not in {"x86_64", "arm64", "universal2"}:
                raise ValueError(f"'arch' has invalid value: {value!r}")
            global_options["macho_arch"] = value
        elif key == "deployment-target":
            if not isinstance(value, str) or re.fullmatch("[0-9]+([.][0-9]+)?", value):
                raise ValueError(f"'deployment-target' has invalid value: {value!r}")
            global_options["deployment_target"] = value
        elif key == "python":
            if not isinstance(value, dict):
                raise ValueError("'python' is not a dictionary")
            for py_key, py_value in value:
                if key in {
                    "use_pythonpath",
                    "use_sitepackages",
                    "use_faulthandler",
                    "verbose",
                }:
                    if not isinstance(py_value, bool):
                        raise ValueError(f"'python.{py_key}' is not a boolean")
                    global_options[py_key] = py_value
                elif py_key == "optimize":
                    if not isinstance(py_value, int):
                        raise ValueError("'python.optimize' is not an integer")
                    global_options["python_optimize"] = py_value
                else:
                    raise ValueError(
                        f"Unknown global configuration option 'python.{py_key}'"
                    )

        else:
            raise ValueError(f"Unknown global configuration option '{key}'")

    if "bundle" not in config:
        raise ValueError("Missing key: 'bundle'")

    bundle_config = config["bundle"]
    if not isinstance(bundle_config, dict) or not all(
        isinstance(item, dict) for item in bundle_config.values()
    ):
        raise ValueError("'bundle' is not a sequence of dicts")

    for bundle_name, bundle_value in bundle_config.items():
        local_options = {
            "plist": {},
            "include": [],
            "exclude": [],
            "dylib-include": [],
            "dylib-exclude": [],
        }
        bundles.append(
            BundleOptions(global_options=result, local_options=local_options)
        )
        for key, value in bundle_value.items():
            if key in {"extension", "name"}:
                if not isinstance(value, str):
                    raise ValueError("'{key}' is not a string")
                local_options[key] = value

            elif key in {"script", "iconfile"}:
                if not isinstance(value, str):
                    raise ValueError("'{key}' is not a string")
                local_options[key] = pathlib.Path(value).resolve()

            elif key in {
                "plugin",
                "chdir",
                "argv-emulator",
                "emulate-shell-environment",
                "redirect-to-asl",
                "stip",
            }:
                if not isinstance(value, bool):
                    raise ValueError("'{key}' is not a boolean")
                local_options[key] = value

            elif key == "resources":
                # XXX: Parse/validate resource structure
                local_options[key] = value

            elif key == "plist":
                if isinstance(value, str):
                    # Load plist path
                    value = {}
                elif not isinstance(value, dict):
                    raise ValueError("'{key}' is not a dict or string")

                local_options[key] = value

            elif key in {"include", "exclude", "dylib-include", "dylib-exclude"}:
                if not isinstance(value, list) or not all(
                    isinstance(item, str) for item in value
                ):
                    raise ValueError(f"{key} is not a list of string")
                local_options[key] = value

            elif key == "extra-scripts":
                if not isinstance(value, list) or not all(
                    isinstance(item, str) for item in value
                ):
                    raise ValueError(f"{key} is not a list of string")
                local_options[key] = [pathlib.Path(item).resolve for item in value]

            # XXX: From her to end is replication of 'global options', refactor
            elif key == "arch":
                if value not in {"x86_64", "arm64", "universal2"}:
                    raise ValueError(f"'arch' has invalid value: {value!r}")
                local_options["macho_arch"] = value

            elif key == "deployment-target":
                if not isinstance(value, str) or re.fullmatch(
                    "[0-9]+([.][0-9]+)?", value
                ):
                    raise ValueError(
                        f"'deployment-target' has invalid value: {value!r}"
                    )
                local_options["deployment_target"] = value

            elif key == "python":
                if not isinstance(value, dict):
                    raise ValueError("'python' is not a dictionary")
                for py_key, py_value in value:
                    if key in {
                        "use_pythonpath",
                        "use_sitepackages",
                        "use_faulthandler",
                        "verbose",
                    }:
                        if not isinstance(py_value, bool):
                            raise ValueError(f"'python.{py_key}' is not a boolean")
                        local_options[py_key] = py_value
                    elif key == "optimize":
                        if not isinstance(py_value, int):
                            raise ValueError("'python.optimize' is not an integer")
                        local_options["python_optimize"] = py_value
                    else:
                        raise ValueError(
                            f"Unknown global configuration option 'python.{py_key}'"
                        )

            else:
                raise ValueError(f"Invalid key 'bundle.{bundle_name}.{key}'")

            if "script" not in local_options:
                raise ValueError(f"Missing 'script' in 'bundle.{bundle_name}'")

        if "extension" not in local_options:
            local_options["extension"] = (
                ".plugin" if local_options.get("plugin") else ".app"
            )

        if "chdir" not in local_options:
            local_options["chdir"] = bool(local_options.get("plugin"))

    return result


if __name__ == "__main__":
    import tomllib

    with open("example.toml", "rb") as stream:
        file_contents = tomllib.load(stream)
    print(parse_pyproject(file_contents))
