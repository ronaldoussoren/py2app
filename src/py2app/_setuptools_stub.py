"""
This module is a backward compatibility
stub that implements the setuptools command
for py2app.

XXX:
    - finish implementation
    - add option for generating a pyrpoject.toml
    - target.prescripts (although current impl. is buggy)
"""

import collections.abc
import pathlib
import plistlib
import shlex
import sys
import sysconfig
import typing
from distutils.errors import DistutilsOptionError
from io import StringIO

from setuptools import Command, Distribution

from . import _config


class _ScriptInfo(typing.TypedDict, total=False):
    script: str
    plist: dict
    extra_scripts: typing.List[str]


def fancy_split(name: str, s: typing.Any) -> typing.List[str]:
    # a split which also strips whitespace from the items
    # passing a list or tuple will return it unchanged
    # This accepts "Any" because the value is passed through setup.py
    if s is None:
        return []
    elif isinstance(s, str):
        return [item.strip() for item in s.split(",")]
    elif isinstance(s, collections.abc.Sequence):
        result: typing.List[str] = []
        for item in s:
            if isinstance(item, str):
                result.append(item)
            else:
                raise DistutilsOptionError(
                    f"invalid value for {name!r}: {item!r} is not a string"
                )

        return result
    else:
        raise DistutilsOptionError(f"invalid value for {name!r}")


class Target:
    # XXX: Target class is not necessary, remove it and related functions.
    script: str
    prescripts: typing.List[typing.Union[str, StringIO]]
    extra_scripts: typing.List[str]
    appdir: str

    def __init__(self, **kw: typing.Any) -> None:  # XXX
        self.__dict__.update(kw)
        # If modules is a simple string, assume they meant list
        m = self.__dict__.get("modules")
        if m and isinstance(m, str):
            self.modules = [m]

        if not hasattr(self, "extra_scripts"):
            self.extra_scripts = []

    def __repr__(self) -> str:
        return f"<Target {self.__dict__}>"


def fixup_targets(
    targets: typing.Sequence[typing.Union[str, _ScriptInfo, Target]],
    default_attribute: str,
) -> typing.Sequence[Target]:
    if not targets:
        return []

    if isinstance(targets, str):
        raise DistutilsOptionError("Target definition should be a sequence")

    ret = []
    for target_def in targets:
        if isinstance(target_def, str):
            # Create a default target object, with the string as the attribute
            target = Target(**{default_attribute: target_def})
        else:
            if isinstance(target_def, dict):
                d = target_def
            else:
                d = typing.cast(_ScriptInfo, target_def.__dict__)
            if default_attribute not in d:
                raise DistutilsOptionError(
                    "This target class requires an attribute '%s'"
                    % (default_attribute,)
                )
            target = Target(**d)
        ret.append(target)
    return ret


class Py2appDistribution(Distribution):
    # Type is only present to help with type checking, the attributes
    # are dynamically added to the Distribution by setuptools.

    app: typing.Sequence[typing.Union[str, _ScriptInfo, "Target"]]
    plugin: typing.Sequence[typing.Union[str, _ScriptInfo, "Target"]]

    def __new__(self) -> "Py2appDistribution":
        raise RuntimeError("Don't instantiate!")

    def get_version(self) -> str:
        ...

    def get_name(self) -> str:
        ...


def finalize_distribution_options(dist: Py2appDistribution) -> None:
    """
    setuptools.finalize_distribution_options extension
    point for py2app, to deal with autodiscovery in
    setuptools 61.

    This addin will set the name and py_modules attributes
    when a py2app distribution is detected that does not
    yet have these attributes.
    are not already set
    """
    if getattr(dist, "app", None) is None and getattr(dist, "plugin", None) is None:
        return

    if getattr(dist.metadata, "py_modules", None) is None:
        dist.py_modules = []

    name = getattr(dist.metadata, "name", None)
    if name is None or name == "UNKNOWN":
        targets: typing.Sequence[Target]
        if dist.app:  # type: ignore
            targets = fixup_targets(dist.app, "script")  # type: ignore
        else:
            targets = fixup_targets(dist.plugin, "script")  # type: ignore

        if not targets:
            return

        name = targets[0].script
        if "." in name:
            name = name.rsplit(".", 1)[0]
        dist.metadata.name = name


class py2app(Command):
    config: _config.Py2appConfiguration

    description = "create a macOS application or plugin from Python scripts"
    user_options = [
        ("app=", None, "application bundle to be built"),
        ("plugin=", None, "plugin bundle to be built"),
        ("includes=", "i", "comma-separated list of modules to include"),
        ("packages=", "p", "comma-separated list of packages to include"),
        (
            "maybe-packages=",
            "p",
            "comma-separated list of packages that will be added outside of the zip file when detected as a dependency",
        ),
        ("iconfile=", None, "Icon file to use"),
        ("excludes=", "e", "comma-separated list of modules to exclude"),
        (
            "dylib-excludes=",
            "E",
            "comma-separated list of frameworks or dylibs to exclude",
        ),
        (
            "optimize=",
            "O",
            'optimization level: -O1 for "python -O", '
            '-O2 for "python -OO", and -O0 to disable [default: -O0]',
        ),
        ("datamodels=", None, "xcdatamodels to be compiled and copied into Resources"),
        (
            "expected-missing-imports=",
            None,
            "expected missing imports either a comma sperated list "
            "or @ followed by file containing a list of imports, one per line",
        ),
        (
            "mappingmodels=",
            None,
            "xcmappingmodels to be compiled and copied into Resources",
        ),
        (
            "resources=",
            "r",
            "comma-separated list of additional data files and folders to "
            "include (not for code!)",
        ),
        (
            "frameworks=",
            "f",
            "comma-separated list of additional frameworks and dylibs to " "include",
        ),
        ("plist=", "P", "Info.plist template file, dict, or plistlib.Plist"),
        (
            "extension=",
            None,
            "Bundle extension [default:.app for app, .plugin for plugin]",
        ),
        ("graph", "g", "output module dependency graph"),
        ("xref", "x", "output module cross-reference as html"),
        (
            "chdir",
            None,
            "change to the data directory (Contents/Resources) "
            "[default for application]",
        ),
        (
            "no-chdir",
            "C",
            "do not change to the data directory (Contents/Resources) "
            "[forced for plugins]",
        ),
        (
            "semi-standalone",
            "s",
            f"depend on an existing installation of Python {sys.version_info[0]}.{sys.version_info[1]}",
        ),
        ("alias", "A", "Use an alias to current source file (for development only!)"),
        ("argv-emulation", "a", "Use argv emulation [disabled for plugins]."),
        (
            "no-argv-emulation",
            "a",
            "Do not use argv emulation [default, forced for plugins].",
        ),
        ("argv-inject=", None, "Inject some commands into the argv"),
        (
            "emulate-shell-environment",
            None,
            "Emulate the shell environment you get in a Terminal window",
        ),
        (
            "no-emulate-shell-environment",
            None,
            "Do not emulate the shell environment (default)",
        ),
        (
            "use-pythonpath",
            None,
            "Allow PYTHONPATH to effect the interpreter's environment",
        ),
        (
            "no-use-pythonpath",
            None,
            "Do not allow PYTHONPATH to effect the interpreter's environment (default)",
        ),
        (
            "use-faulthandler",
            None,
            "Enable the faulthandler in the generated bundle (Python 3.3+)",
        ),
        (
            "no-use-faulthandler",
            None,
            "Disable the faulthandler in the generated bundle (Python 3.3+, default)",
        ),
        ("verbose-interpreter", None, "Start python in verbose mode"),
        ("no-verbose-interpreter", None, "Start python in regular mode (default)"),
        ("bdist-base=", "b", "base directory for build library (default is build)"),
        (
            "dist-dir=",
            "d",
            "directory to put final built distributions in (default is dist)",
        ),
        (
            "site-packages",
            None,
            "include the system and user site-packages into sys.path",
        ),
        (
            "no-site-packages",
            None,
            "do not include the system and user site-packages into sys.path (default)",
        ),
        (
            "strip",
            "S",
            "strip debug and local symbols from output (on by default, for "
            "compatibility)",
        ),
        ("no-strip", None, "do not strip debug and local symbols from output"),
        (
            "arch=",
            None,
            "set of architectures to use (x86_64, arm64, universal2; "
            f"default is {sysconfig.get_platform().split('-')[-1]!r})",
        ),
        (
            "qt-plugins=",
            None,
            "set of Qt plugins to include in the application bundle " "(default None)",
        ),
        (
            "matplotlib-backends=",
            None,
            "set of matplotlib backends to include (default: all)",
        ),
        (
            "extra-scripts=",
            None,
            "set of additional scripts to include in the application bundle",
        ),
        ("include-plugins=", None, "List of plugins to include"),
        (
            "report-missing-from-imports",
            None,
            "Report the list of missing names for 'from module import name'",
        ),
        (
            "no-report-missing-conditional-import",
            None,
            "Don't report missing modules from conditional imports",
        ),
        (
            "redirect-stdout-to-asl",
            None,
            "Forward the stdout/stderr streams to Console.app using ASL",
        ),
        (
            "no-redirect-stdout-to-asl",
            None,
            "Don't the stdout/stderr streams to Console.app using ASL (default)",
        ),
    ]

    boolean_options = [
        "xref",
        "strip",
        "no-strip",
        "site-packages",
        "no-site-packages",
        "semi-standalone",
        "alias",
        "argv-emulation",
        "no-argv-emulation",
        "use-pythonpath",
        "no-use-pythonpath",
        "use-faulthandler",
        "no-use-faulthandler",
        "verbose-interpreter",
        "no-verbose-interpreter",
        "chdir",
        "no-chdir",
        "graph",
        "emulate-shell-environment",
        "no-emulate-shell-environment",
        "report-missing-from-imports",
        "no-report-missing-conditional-import",
        "redirect-stdout-to-asl",
        "no-redirect-stdout-to-asl",
    ]

    negative_opt = {
        "no-strip": "strip",
        "no-chdir": "chdir",
        "no-emulate-shell-environment": "emulate-shell-environment",
        "no-redirect-stdout-to-asl": "redirect-stdout-to-asl",
        "no-argv-emulation": "argv-emulation",
        "no-use-pythonpath": "use-pythonpath",
        "no-use-faulthandler": "use-faulthandler",
        "no-site-packages": "site-packages",
        "no-verbose-interpreter": "verbose-interpreter",
    }

    def initialize_options(self) -> None:
        self.app = None
        self.plugin = None
        self.optimize = None
        self.bdist_base = None
        self.xref = False
        self.graph = False
        self.arch = None
        self.strip = None
        self.iconfile = None
        self.extension = None
        self.alias = False
        self.argv_emulation = None
        self.emulate_shell_environment = None
        self.argv_inject = None
        self.chdir = None
        self.site_packages = None
        self.use_pythonpath = None
        self.use_faulthandler = None
        self.verbose_interpreter = None
        self.includes = None
        self.packages = None
        self.maybe_packages = None
        self.excludes = None
        self.dylib_excludes = None
        self.frameworks = None
        self.resources = None
        self.datamodels = None
        self.mappingmodels = None
        self.plist = None
        self.compressed = None
        self.semi_standalone = False
        self.dist_dir = None
        self.debug_skip_macholib = None
        self.debug_modulegraph = None
        self.filters = None
        self.qt_plugins = None
        self.matplotlib_backends = None
        self.extra_scripts = None
        self.include_plugins = None
        self.report_missing_from_imports = False
        self.no_report_missing_conditional_import = False
        self.redirect_stdout_to_asl = None
        self.expected_missing_imports = None

    def finalize_options(self) -> None:
        self.warnings = []
        # XXX: Reorder the initialisation of the option dictionaries.

        # XXX: dist directories are not yet used in configuration
        self.set_undefined_options(
            "bdist", ("dist_dir", "dist_dir"), ("bdist_base", "bdist_base")
        )

        recipe_options = {"zip-unsafe": []}
        global_options = {}

        # the setuptools interface allows for exactly 1 bundle configuration
        bundle_options = {}
        bundles = []
        self.config = _config.Py2appConfiguration(
            bundles, global_options, _config.RecipeOptions(recipe_options)
        )

        bundles.append(
            _config.BundleOptions(
                global_options=self.config, local_options=bundle_options
            )
        )

        # Global options
        if self.strip is not None:
            if not isinstance(self.strip, (int, bool)):
                # The documented interface uses "bool", but setuptools option
                # parsing will set the attribute to an integer.
                raise DistutilsOptionError("Strip is not a boolean")

            global_options["strip"] = bool(self.strip)

        # Recipe options

        recipe_options["qt-plugins"] = fancy_split("qt-plugins", self.qt_plugins)
        recipe_options["matplotlib-backends"] = fancy_split(
            "matplotlib-backends", self.matplotlib_backends
        )

        # Bundle options
        #   The setuptools interface supports only one bundle.

        dist = self.distribution
        if self.app is not None:
            app = fixup_targets(self.app, "script")
        else:
            app = fixup_targets(dist.app, "script")

        if self.plugin is not None:
            plugin = fixup_targets(self.plugin, "script")
        else:
            plugin = fixup_targets(dist.plugin, "script")

        if app and plugin:
            raise DistutilsOptionError(
                "You must specify either app or plugin, not both"
            )

        if app:
            if len(app) != 1:
                raise DistutilsOptionError("Multiple targets not currently supported")

            bundle_options["plugin"] = False
            if "extension" not in bundle_options:
                bundle_options["extension"] = ".app"
            bundle_options["script"] = pathlib.Path(app[0].script)
            extra_scripts = app[0].extra_scripts
            if self.chdir is not None:
                bundle_options["chdir"] = bool(self.chdir)
            else:
                bundle_options["chdir"] = True

        elif plugin:
            if len(plugin) != 1:
                raise DistutilsOptionError("Multiple targets not currently supported")
            bundle_options["plugin"] = True
            if "extension" not in bundle_options:
                bundle_options["extension"] = ".bundle"
            if self.chdir is not None:
                bundle_options["chdir"] = bool(self.chdir)
            else:
                bundle_options["chdir"] = False

            bundle_options["script"] = pathlib.Path(plugin[0].script)
            extra_scripts = plugin[0].extra_scripts

        if not isinstance(extra_scripts, collections.abc.Sequence) or not all(
            isinstance(item, str) for item in extra_scripts
        ):
            raise DistutilsOptionError(
                "Target 'extra_scripts' is not a list of strings"
            )
        bundle_options["extra-scripts"] = [
            pathlib.Path(".") / item for item in extra_scripts
        ]

        if not isinstance(self.semi_standalone, (bool, int)):
            raise DistutilsOptionError("Invalid configuration for 'semi-standalone'")
        if not isinstance(self.alias, (bool, int)):
            raise DistutilsOptionError("Invalid configuration for 'alias'")

        if self.semi_standalone and self.alias:
            raise DistutilsOptionError("Cannot have both alias and semi-standalone")

        if self.semi_standalone:
            bundle_options["build-type"] = _config.BuildType.SEMI_STANDALONE
        elif self.alias:
            bundle_options["build-type"] = _config.BuildType.ALIAS
        else:
            # Use the global default, which is STANDALONE.
            pass

        if self.argv_inject is not None:
            if isinstance(self.argv_inject, str):
                try:
                    bundle_options["argv-inject"] = shlex.split(self.argv_inject)
                except ValueError:
                    raise DistutilsOptionError(
                        "Invalid configuration for 'argv-inject'"
                    )
            elif isinstance(self.argv_inject, collections.abc.Sequence) and all(
                isinstance(item, str) for item in self.argv_inject
            ):
                bundle_options["argv-inject"] = list(self.argv_inject)
            else:
                raise DistutilsOptionError("Invalid configuration for 'argv-inject'")
        else:
            bundle_options["argv-inject"] = []

        bundle_options["include"] = fancy_split("includes", self.includes)
        packages = fancy_split("packages", self.packages)
        bundle_options["include"].extend(packages)
        bundle_options["full-package"] = fancy_split(
            "maybe-packages", self.maybe_packages
        )
        bundle_options["full-package"].extend(packages)

        bundle_options["exclude"] = fancy_split("excludes", self.excludes)
        bundle_options["dylib-exclude"] = fancy_split(
            "dylib-excludes", self.dylib_excludes
        )
        bundle_options["dylib-include"] = fancy_split("frameworks", self.frameworks)

        try:
            bundle_options["resources"] = [
                _config.Resource.from_item(item)
                for item in fancy_split("resources", self.resources)
            ]
        except _config.ConfigurationError:
            raise DistutilsOptionError("Invalid value for 'resources'")

        for attr in ("datamodels", "mappingmodels"):
            if getattr(self, attr):
                self.warnings.append(
                    f"WARNING: the {attr} option is deprecated, "
                    "add model files to the list of resources"
                )
            try:
                bundle_options["resources"].extend(
                    [
                        _config.Resource.from_item(item)
                        for item in fancy_split(attr, getattr(self, attr))
                    ]
                )
            except _config.ConfigurationError:
                raise DistutilsOptionError(f"Invalid value for '{attr}'")

        for attr, key in [
            ("redirect_stdout_to_asl", "redirect-to-asl"),
            ("use_pythonpath", "python.use-pythonpath"),
            ("use_faulthandler", "python.use-faulthandler"),
            ("site_packages", "python.use-sitepackages"),
            ("argv_emulation", "argv-emulator"),
            ("verbose_interpreter", "python.verbose"),
        ]:
            value = getattr(self, attr)
            if value is not None:
                if not isinstance(value, (bool, int)):
                    raise DistutilsOptionError(f"Invalid value for '{attr}'")
                bundle_options[key] = bool(value)

        if self.plist is None:
            bundle_options["plist"] = {}

        elif isinstance(self.plist, str):
            try:
                with open(self.plist, "rb") as fp:
                    bundle_options["plist"] = plistlib.load(fp)

            except OSError:
                raise DistutilsOptionError(f"Cannot open plist file {self.plist!r}")
            except plistlib.InvalidFileException:
                raise DistutilsOptionError(f"Invalid plist file {self.plist!r}")

        elif isinstance(self.plist, dict):
            try:
                plistlib.dumps(self.plist)
            except Exception:
                raise DistutilsOptionError("Cannot serialize 'plist' value")

            bundle_options["plist"] = self.plist

        else:
            raise DistutilsOptionError("Invalid value for 'plist'")

        if self.emulate_shell_environment is not None:
            bundle_options["emulate-shell-environment"] = bool(
                self.emulate_shell_environment
            )

        if isinstance(self.iconfile, str):
            bundle_options["iconfile"] = pathlib.Path(self.iconfile)
        elif self.iconfile is not None:
            raise DistutilsOptionError("Invalid value for 'iconfile'")

        bundle_options["extra-scripts"].extend(
            [
                pathlib.Path(".") / item
                for item in fancy_split("extra-scripts", self.extra_scripts)
            ]
        )

        # XXX: Not yet present in new configuration
        # self.include_plugins = fancy_split("include-plugins", self.include_plugins)

    def run(self):
        if self.warnings:
            for w in self.warnings:
                print(w)
        print(self.config)

        # XXX: Invoke the new builder with self.config
