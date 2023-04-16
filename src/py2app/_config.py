"""
Representation of the py2app configuration.

XXX: It should be possible to simplify this code
     a lot.
XXX: Should this module validate existence of paths?
"""

import enum
import pathlib
import plistlib
import re
import sys
import sysconfig
import typing

T = typing.TypeVar("T")

_, _DEFAULT_TARGET, _DEFAULT_ARCH = sysconfig.get_platform().split("-")


class ConfigurationError(Exception):
    """
    Invalid configuration detected.
    """

    pass


class BuildType(enum.Enum):
    STANDALONE = "standalone"
    ALIAS = "alias"

    # XXX: Still support semi-standalone?
    SEMI_STANDALONE = "semi-standalone"


class BuildArch(enum.Enum):
    ARM64 = "arm64"
    X86_64 = "x86_64"
    UNIVERSAL2 = "universal2"


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
        except AttributeError:
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


class Resource:
    __slots__ = {
        "destination": "Destination, relative to the Resources folder",
        "sources": "Source paths relative to the configuration folder",
    }

    def __repr__(self):
        return f"<Resource destination={self.destination!r} sources={self.sources!r}>"

    @classmethod
    def from_config(
        cls, config_item: typing.Any, config_root: pathlib.Path, location: str
    ):
        if isinstance(config_item, str):
            return cls(pathlib.Path("."), [config_root / config_item])
        elif isinstance(config_item, (list, tuple)):
            if len(config_item) != 2:
                raise ConfigurationError(f"{location}: invalid item {config_item!r}")
            dst, src = config_item
            if (
                not isinstance(dst, str)
                or not isinstance(src, list)
                or not all(isinstance(item, str) for item in src)
            ):
                raise ConfigurationError(f"{location}: invalid item {config_item!r}")
            return cls(pathlib.Path(dst), [config_root / s for s in src])
        else:
            raise ConfigurationError(f"{location}: invalid item {config_item!r}")

    def __init__(
        self, destination: pathlib.Path, sources: typing.Sequence[pathlib.Path]
    ):
        self.destination = destination
        self.sources = list(sources)

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        if not isinstance(other, Resource):
            return False

        return (self.destination == other.destination) and (
            self.sources == other.sources
        )


class BundleOptions:
    def __init__(self, global_options, local_options):
        self._global = global_options
        self._local = local_options

    build_type = inherited[BuildType]("build-type", "build_type")
    macho_strip = inherited[bool]("strip", "macho_strip")
    macho_arch = inherited[BuildArch]("arch", "macho_arch")
    deployment_target = inherited[str]("deployment-target", "deployment_target")
    python_optimize = inherited[int]("python.optimize", "python_optimize")
    python_verbose = inherited[bool]("python.verbose", "python_verbose")
    python_use_pythonpath = inherited[bool](
        "python.use-pythonpath", "python_use_pythonpath"
    )
    python_use_sitepackages = inherited[bool](
        "python.use-sitepackages", "python_use_sitepackages"
    )
    python_use_faulthandler = inherited[bool](
        "python.use-faulthandler", "python_use_faulthandler"
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

    # Python modules or packages to include unconditionally:
    py_include = local[typing.Sequence[str]]("include", ())

    # Python modules or packages to exclude unconditionally:
    py_exclude = local[typing.Sequence[str]]("exclude", ())

    # Python packages that will be included in their entirety
    # when they are a dependency.
    py_full_package = local[typing.Sequence[str]]("full-package", ())

    macho_include = local[typing.Sequence[str]]("dylib-include", ())  # XXX: Path?
    macho_exclude = local[typing.Sequence[str]]("dylib-exclude", ())  # XXX: Path?

    chdir = local[bool]("chdir")
    argv_emulator = local[bool]("argv-emulator", False)
    argv_inject = local[typing.Sequence[str]]("argv-inject", ())
    emulate_shell_environment = local[bool]("emulate-shell-environment", False)
    redirect_to_asl = local[bool]("redirect-to-asl", False)

    def __repr__(self):
        result = []
        result.append("<BundleOptions\n")
        result.append(f"  build_type = {self.build_type}\n")
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
        result.append(f"  py_full_package = {self.py_full_package!r}\n")
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
    matplotlib_backends = local[typing.Optional[typing.Sequence[str]]](
        "matplotlib-backends", None
    )

    def __repr__(self):
        result = []
        result.append("<RecipeOptions\n")
        result.append(f"  zip_unsafe = {self.zip_unsafe!r}\n")
        result.append(f"  qt_plugins = {self.qt_plugins!r}\n")
        result.append(f"  matplotlib_backends = {self.matplotlib_backends!r}\n")

        result.append(">")
        return "".join(result)


class Py2appConfiguration:
    def __init__(self, bundles, global_options, recipe_options):
        self._local = global_options
        self.bundles = bundles
        self.recipe = recipe_options

    build_type = local[BuildType]("build-type", BuildType.STANDALONE)
    deployment_target = local[str]("deployment-target", _DEFAULT_TARGET)
    macho_strip = local[bool]("strip", True)
    macho_arch = local[BuildArch]("arch", BuildArch(_DEFAULT_ARCH))
    python_optimize = local[int]("python.optimize", sys.flags.optimize)
    python_verbose = local[bool]("python.verbose", bool(sys.flags.verbose))
    python_use_pythonpath = local[bool]("python.use-pythonpath", False)
    python_use_sitepackages = local[bool]("python.use-sitepackages", False)
    python_use_faulthandler = local[bool]("python.use-faulthandler", False)

    def __repr__(self):
        result = []
        result.append("<Py2appConfiguration\n")
        result.append(f"  deployment_target = {self.deployment_target!r}\n")
        result.append(f"  macho_strip = {self.macho_strip!r}\n")
        result.append(f"  macho_arch = {self.macho_arch!r}\n")
        result.append(f"  python_optimize = {self.python_optimize!r}\n")
        result.append(f"  python_verbose = {self.python_verbose!r}\n")
        result.append(f"  python_use_pythonpath = {self.python_use_pythonpath!r}\n")
        result.append(f"  python_use_sitepackages = {self.python_use_sitepackages!r}\n")
        result.append(f"  python_use_faulthandler = {self.python_use_faulthandler!r}\n")
        result.append(f"  build_type = {self.build_type}\n")
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
                if cur:
                    result.append(f"    {cur}\n")
                else:
                    result.append("\n")
            result.append("    >,\n")
        result.append("  ]\n")

        result.append(">")
        return "".join(result)


def parse_pyproject(file_contents: dict, config_root: pathlib.Path):
    try:
        config = file_contents["tool"]["py2app"]
    except KeyError:
        raise ConfigurationError(
            "Configuration doesn't contain a 'tool.py2app' key"
        ) from None

    global_options = {}
    recipe_options = {"zip-unsafe": []}
    bundles = []

    result = Py2appConfiguration(bundles, global_options, RecipeOptions(recipe_options))
    for key, value in config.items():
        if key in {"bundle"}:
            continue
        elif key == "recipe":
            if not isinstance(config["recipe"], dict):
                raise ConfigurationError("'tool.py2app.recipe' is not a dictionary")
            for py_key, py_value in config["recipe"].items():
                if py_key in {"zip-unsafe", "qt-plugins", "matplotlib-backends"}:
                    if not isinstance(py_value, list) or not all(
                        isinstance(v, str) for v in py_value
                    ):
                        raise ConfigurationError(
                            f"'tool.py2app.recipe.{py_key}' is not a list of strings"
                        )
                    recipe_options[py_key] = py_value
                else:
                    raise ConfigurationError(
                        f"'tool.py2app.recipe.{py_key}' is not a valid key"
                    )

        elif key == "build-type":
            try:
                global_options["build-type"] = BuildType(value)
            except ValueError:
                raise ConfigurationError(
                    "'tool.py2app.build-type' has invalid value"
                ) from None

        elif key == "strip":
            if not isinstance(value, bool):
                raise ConfigurationError("'tool.py2app.strip' is not a boolean")
            global_options["strip"] = value
        elif key == "arch":
            try:
                global_options["arch"] = BuildArch(value)
            except ValueError:
                raise ConfigurationError("'tool.py2app.arch' has invalid value")
        elif key == "deployment-target":
            if (
                not isinstance(value, str)
                or re.fullmatch("[0-9]+([.][0-9]+)?", value) is None
            ):
                raise ConfigurationError("'tool.py2app.deployment-target' is not valid")
            global_options[key] = value
        elif key == "python":
            if not isinstance(value, dict):
                raise ConfigurationError("'tool.py2app.python' is not a dictionary")
            for py_key, py_value in value.items():
                if py_key in {
                    "use-pythonpath",
                    "use-sitepackages",
                    "use-faulthandler",
                    "verbose",
                }:
                    if not isinstance(py_value, bool):
                        raise ConfigurationError(
                            f"'tool.py2app.python.{py_key}' is not a boolean"
                        )
                    global_options[f"python.{py_key}"] = py_value
                elif py_key == "optimize":
                    if not isinstance(py_value, int):
                        raise ConfigurationError(
                            "'tool.py2app.python.optimize' is not an integer"
                        )
                    global_options["python.optimize"] = py_value
                else:
                    raise ConfigurationError(
                        f"invalid key 'tool.py2app.python.{py_key}'"
                    )

        else:
            raise ConfigurationError(f"invalid key 'tool.py2app.{key}'")

    if "bundle" not in config:
        raise ConfigurationError("missing key: 'tool.py2app.bundle'")

    bundle_config = config["bundle"]
    if not isinstance(bundle_config, dict) or not all(
        isinstance(item, dict) for item in bundle_config.values()
    ):
        raise ConfigurationError("'tool.py2app.bundle' is not a sequence of dicts")

    for bundle_name, bundle_value in bundle_config.items():
        local_options = {
            "plist": {},
            "include": [],
            "exclude": [],
            "full-package": [],
            "dylib-include": [],
            "dylib-exclude": [],
        }
        bundles.append(
            BundleOptions(global_options=result, local_options=local_options)
        )
        for key, value in bundle_value.items():
            if key in {"extension", "name"}:
                if not isinstance(value, str):
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.{key}' is not a string"
                    )
                local_options[key] = value

            elif key in {"script", "iconfile"}:
                if not isinstance(value, str):
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.{key}' is not a string"
                    )
                local_options[key] = config_root / pathlib.Path(value)

            elif key in {
                "plugin",
                "chdir",
                "argv-emulator",
                "emulate-shell-environment",
                "redirect-to-asl",
                "strip",
            }:
                if not isinstance(value, bool):
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.{key}' is not a boolean"
                    )
                local_options[key] = value

            elif key == "resources":
                if not isinstance(value, list):
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.{key}' is not a list"
                    )

                # XXX: Should this merge "Resource" definitions for the same destination?
                local_options[key] = [
                    Resource.from_config(
                        item, config_root, f"'tool.py2app.bundle.{bundle_name}.{key}"
                    )
                    for item in value
                ]

            elif key == "plist":
                if isinstance(value, str):
                    # Load plist path
                    try:
                        with open(config_root / value, "rb") as stream:
                            value = plistlib.load(stream)

                    except OSError:
                        raise ConfigurationError(
                            f"'tool.py2app.bundle.{bundle_name}.{key}' cannot open {value!r}"
                        )
                    except plistlib.InvalidFileException:
                        raise ConfigurationError(
                            f"'tool.py2app.bundle.{bundle_name}.{key}' invalid plist file"
                        )

                elif isinstance(value, dict):
                    # Check that the value can be serialized as a plist
                    try:
                        plistlib.dumps(value)
                    except Exception:
                        raise ConfigurationError(
                            f"'tool.py2app.bundle.{bundle_name}.{key}' invalid plist contents"
                        )

                else:
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.{key}' is not a dict or string"
                    )

                local_options[key] = value

            elif key in {
                "include",
                "exclude",
                "full-package",
                "dylib-include",
                "dylib-exclude",
                "argv-inject",
            }:
                if not isinstance(value, list) or not all(
                    isinstance(item, str) for item in value
                ):
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.{key}' is not a list of string"
                    )
                local_options[key] = value

            elif key == "extra-scripts":
                if not isinstance(value, list) or not all(
                    isinstance(item, str) for item in value
                ):
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.{key}' is not a list of string"
                    )
                local_options[key] = [
                    config_root / pathlib.Path(item) for item in value
                ]

            # XXX: From her to end is replication of 'global options', refactor
            elif key == "build-type":
                try:
                    local_options["build-type"] = BuildType(value)
                except ValueError:
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.build-type' has invalid value"
                    ) from None

            elif key == "arch":
                if value not in {"x86_64", "arm64", "universal2"}:
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.arch' has invalid value"
                    )
                local_options["arch"] = BuildArch(value)

            elif key == "deployment-target":
                if (
                    not isinstance(value, str)
                    or re.fullmatch(r"[0-9]+([.][0-9]+)?", value) is None
                ):
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.deployment-target' is not valid"
                    )
                local_options[key] = value

            elif key == "python":
                if not isinstance(value, dict):
                    raise ConfigurationError(
                        f"'tool.py2app.bundle.{bundle_name}.python' is not a dictionary"
                    )
                for py_key, py_value in value.items():
                    if py_key in {
                        "use-pythonpath",
                        "use-sitepackages",
                        "use-faulthandler",
                        "verbose",
                    }:
                        if not isinstance(py_value, bool):
                            raise ConfigurationError(
                                f"'tool.py2app.bundle.{bundle_name}.python.{py_key}' is not a boolean"
                            )
                        local_options[f"python.{py_key}"] = py_value
                    elif py_key == "optimize":
                        if not isinstance(py_value, int):
                            raise ConfigurationError(
                                f"'tool.py2app.bundle.{bundle_name}.python.optimize' is not an integer"
                            )
                        local_options["python.optimize"] = py_value
                    else:
                        raise ConfigurationError(
                            f"invalid key: 'tool.py2app.bundle.{bundle_name}.python.{py_key}'"
                        )

            else:
                raise ConfigurationError(
                    f"invalid key 'tool.py2app.bundle.{bundle_name}.{key}'"
                )

        if "script" not in local_options:
            raise ConfigurationError(
                f"missing 'script' in 'tool.py2app.bundle.{bundle_name}'"
            )

        if "extension" not in local_options:
            local_options["extension"] = (
                ".plugin" if local_options.get("plugin") else ".app"
            )

        if "chdir" not in local_options:
            local_options["chdir"] = not bool(local_options.get("plugin"))

    return result
