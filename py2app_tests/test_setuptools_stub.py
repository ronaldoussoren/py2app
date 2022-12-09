# XXX: This currently uses "py2app2" as the command name, change
#      later (global search & replace)
import io
import pathlib
import plistlib
import sys
from distutils import errors
from unittest import TestCase, mock

import setuptools

from py2app import _config

NOT_SET = object()


class TestSetuptoolsConfiguration(TestCase):
    # This class tests the argument parsing of
    # the setuptools compatibility stub.

    def setUp(self):
        # Setuptools picks up configuration from  pyproject.toml
        # and that messes up these tests..
        #
        # This is a pretty crude hack...
        self._patcher = mock.patch(
            "setuptools.dist.Distribution._get_project_config_files",
            spec=True,
            return_value=([], []),
        )
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    def assert_config_types(self, config):
        # Check that the py2app configuration has fields of the right
        # type, the core code assumes that types are correct.
        self.assertIsInstance(config, _config.Py2appConfiguration)

        self.assertIsInstance(config.build_type, _config.BuildType)

        self.assertIsInstance(config.deployment_target, str)
        self.assertRegex(config.deployment_target, r"^\d+([.]\d+)$")

        self.assertIsInstance(config.macho_strip, bool)
        self.assertIsInstance(config.macho_arch, _config.BuildArch)

        self.assertIsInstance(config.python_optimize, int)
        self.assertIsInstance(config.python_verbose, bool)
        self.assertIsInstance(config.python_use_pythonpath, bool)
        self.assertIsInstance(config.python_use_sitepackages, bool)
        self.assertIsInstance(config.python_use_faulthandler, bool)

        self.assertIsInstance(config.recipe, _config.RecipeOptions)
        self.assertIsInstance(config.recipe.zip_unsafe, list)
        self.assertTrue(all(isinstance(item, str) for item in config.recipe.zip_unsafe))

        self.assertIsInstance(config.recipe.qt_plugins, list)
        self.assertTrue(all(isinstance(item, str) for item in config.recipe.qt_plugins))

        self.assertIsInstance(config.recipe.matplotlib_backends, list)
        self.assertTrue(
            all(isinstance(item, str) for item in config.recipe.matplotlib_backends)
        )

        self.assertEqual(len(config.bundles), 1)
        bundle = config.bundles[0]
        self.assertIsInstance(bundle, _config.BundleOptions)
        self.assertIsInstance(bundle.name, str)
        self.assertIsInstance(bundle.script, pathlib.Path)
        self.assertIsInstance(bundle.plugin, bool)
        self.assertIsInstance(bundle.extension, str)
        self.assertIsInstance(bundle.iconfile, (pathlib.Path, type(None)))
        self.assertIsInstance(bundle.resources, list)
        for item in bundle.resources:
            self.assertIsInstance(item, _config.Resource)
            self.assertIsInstance(item.destination, pathlib.Path)
            self.assertIsInstance(item.sources, list)
            self.assertTrue(all(isinstance(v, pathlib.Path) for v in item.sources))

        self.assertIsInstance(bundle.plist, dict)
        plistlib.dumps(bundle.plist)
        self.assertIsInstance(bundle.extra_scripts, list)
        self.assertTrue(
            all(isinstance(item, pathlib.Path) for item in bundle.extra_scripts),
            f"not all extra_scripts items are Paths: {bundle.extra_scripts!r}",
        )
        self.assertIsInstance(bundle.py_include, list)
        self.assertTrue(all(isinstance(item, str) for item in bundle.py_include))
        self.assertIsInstance(bundle.py_exclude, list)
        self.assertTrue(all(isinstance(item, str) for item in bundle.py_exclude))
        self.assertIsInstance(bundle.py_full_package, list)
        self.assertTrue(all(isinstance(item, str) for item in bundle.py_full_package))
        self.assertIsInstance(bundle.macho_include, list)
        self.assertTrue(all(isinstance(item, str) for item in bundle.macho_include))
        self.assertIsInstance(bundle.macho_exclude, list)
        self.assertTrue(all(isinstance(item, str) for item in bundle.macho_exclude))
        self.assertIsInstance(bundle.chdir, bool)
        self.assertIsInstance(bundle.argv_emulator, bool)
        self.assertIsInstance(bundle.argv_inject, list)
        self.assertTrue(all(isinstance(item, str) for item in bundle.argv_inject))
        self.assertIsInstance(bundle.emulate_shell_environment, bool)
        self.assertIsInstance(bundle.redirect_to_asl, bool)

    def assert_recipe_options(
        self, options, *, zip_unsafe=(), qt_plugins=(), matplotlib_backends=()
    ):
        self.assertIsInstance(options, _config.RecipeOptions)
        self.assertIsInstance(options.zip_unsafe, list)
        self.assertIsInstance(options.qt_plugins, list)
        self.assertIsInstance(options.matplotlib_backends, list)

        self.assertCountEqual(options.zip_unsafe, zip_unsafe)
        self.assertCountEqual(options.qt_plugins, qt_plugins)
        self.assertCountEqual(options.matplotlib_backends, matplotlib_backends)

    def assert_bundle_options(
        self,
        options,
        *,
        build_type=NOT_SET,
        macho_strip=NOT_SET,
        macho_arch=NOT_SET,
        deployment_target=NOT_SET,
        python_optimize=NOT_SET,
        python_verbose=NOT_SET,
        python_use_pythonpath=NOT_SET,
        python_use_sitepackages=NOT_SET,
        python_use_faulthandler=NOT_SET,
        name=NOT_SET,
        script=NOT_SET,
        plugin=False,
        extension=NOT_SET,
        iconfile=None,
        resources=(),
        plist=NOT_SET,
        extra_scripts=(),
        py_include=(),
        py_exclude=(),
        py_full_package=(),
        macho_include=(),
        macho_exclude=(),
        chdir=NOT_SET,
        argv_emulator=False,
        argv_inject=(),
        emulate_shell_environment=False,
        redirect_to_asl=False,
    ):
        self.assertIsInstance(options, _config.BundleOptions)
        if build_type is NOT_SET:
            self.assertNotIn("build-type", options._local)
        else:
            self.assertIn("build-type", options._local)
            self.assertEqual(options.build_type, build_type)

        if macho_strip is NOT_SET:
            self.assertNotIn("strip", options._local)
        else:
            self.assertNotIn("strip", options._local)
            self.assertEqual(options.macho_strip, macho_strip)

        if macho_arch is NOT_SET:
            self.assertNotIn("arch", options._local)
        else:
            self.assertIn("arch", options._local)
            self.assertEqual(options.macho_arch, macho_arch)

        if deployment_target is NOT_SET:
            self.assertNotIn("deployment-target", options._local)
        else:
            self.assertIn("deployment-target", options._local)
            self.assertEqual(options.deployment_target, deployment_target)

        if python_optimize is NOT_SET:
            self.assertNotIn("python.optimize", options._local)
        else:
            self.assertIn("python.optimize", options._local)
            self.assertEqual(options.python_optimize, python_optimize)

        if python_verbose is NOT_SET:
            self.assertNotIn("python.verbose", options._local)
        else:
            self.assertIn("python.verbose", options._local)
            self.assertEqual(options.python_verbose, python_verbose)

        if python_use_pythonpath is NOT_SET:
            self.assertNotIn("python.use-pythonpath", options._local)
        else:
            self.assertIn("python.use-pythonpath", options._local)
            self.assertEqual(options.python_use_pythonpath, python_use_pythonpath)

        if python_use_sitepackages is NOT_SET:
            self.assertNotIn("python.use-sitepackages", options._local)
        else:
            self.assertIn("python.use-sitepackages", options._local)
            self.assertEqual(options.python_use_sitepackages, python_use_sitepackages)

        if python_use_faulthandler is NOT_SET:
            self.assertNotIn("python.use-faulthandler", options._local)
        else:
            self.assertIn("python.use-faulthandler", options._local)
            self.assertEqual(options.python_use_faulthandler, python_use_faulthandler)

        if name is NOT_SET:
            self.assertNotIn("name", options._local)
        else:
            self.assertIn("name", options._local)
            self.assertEqual(options.name, name)

        if script is NOT_SET:
            self.assertNotIn("script", options._local)
        else:
            self.assertIn("script", options._local)
            self.assertEqual(options.script, script)

        self.assertEqual(options.plugin, plugin)
        if extension is NOT_SET:
            extension = ".bundle" if options.plugin else ".app"
        self.assertEqual(options.extension, extension)
        self.assertEqual(options.iconfile, iconfile)
        self.assertIsInstance(options.resources, list)
        self.assertCountEqual(options.resources, resources)

        if plist is NOT_SET:
            plist = {}
        self.assertIsInstance(options.plist, dict)
        self.assertEqual(options.plist, plist)

        self.assertIsInstance(options.extra_scripts, list)
        self.assertCountEqual(options.extra_scripts, extra_scripts)

        self.assertIsInstance(options.py_include, list)
        self.assertCountEqual(options.py_include, py_include)

        self.assertIsInstance(options.py_exclude, list)
        self.assertCountEqual(options.py_exclude, py_exclude)

        self.assertIsInstance(options.py_full_package, list)
        self.assertCountEqual(options.py_full_package, py_full_package)

        self.assertIsInstance(options.macho_include, list)
        self.assertCountEqual(options.macho_include, macho_include)

        self.assertIsInstance(options.macho_exclude, list)
        self.assertCountEqual(options.macho_exclude, macho_exclude)

        if chdir is NOT_SET:
            chdir = False if options.plugin else True
        self.assertEqual(options.chdir, chdir)
        self.assertEqual(options.argv_emulator, argv_emulator)

        self.assertIsInstance(options.argv_inject, list)
        self.assertCountEqual(options.argv_inject, argv_inject)

        self.assertEqual(options.emulate_shell_environment, emulate_shell_environment)
        self.assertEqual(options.redirect_to_asl, redirect_to_asl)

    def assert_global_options(
        self,
        options,
        *,
        build_type=_config.BuildType.STANDALONE,
        deployment_target=_config._DEFAULT_TARGET,
        macho_strip=True,
        macho_arch=_config.BuildArch(_config._DEFAULT_ARCH),  # noqa: B008
        python_optimize=sys.flags.optimize,
        python_verbose=bool(sys.flags.verbose),  # noqa: B008
        python_use_pythonpath=False,
        python_use_sitepackages=False,
        python_use_faulthandler=False,
    ):
        self.assertIsInstance(options, _config.Py2appConfiguration)
        self.assertIsInstance(options.recipe, _config.RecipeOptions)
        self.assertIsInstance(options.bundles, list)
        self.assertTrue(
            all(isinstance(item, _config.BundleOptions) for item in options.bundles)
        )

        self.assertEqual(options.build_type, build_type)
        self.assertEqual(options.deployment_target, deployment_target)
        self.assertEqual(options.macho_strip, macho_strip)
        self.assertEqual(options.macho_arch, macho_arch)
        self.assertEqual(options.python_optimize, python_optimize)
        self.assertEqual(options.python_use_pythonpath, python_use_pythonpath)
        self.assertEqual(options.python_use_sitepackages, python_use_sitepackages)
        self.assertEqual(options.python_use_faulthandler, python_use_faulthandler)

    def run_setuptools(self, commandline_options, setup_keywords):
        old_argv = sys.argv
        sys.argv = commandline_options
        try:
            with mock.patch(
                "py2app._setuptools_stub.py2app.run", new_executable=lambda self: None
            ):
                result = setuptools.setup(**setup_keywords)
        finally:
            sys.argv = old_argv

        return result.get_command_obj("py2app2")

    def test_finalize_options(self):
        with self.subTest("basic settings"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={
                    "app": ["script.py"],
                },
            )
            self.assertEqual(command.distribution.metadata.name, "script")

        with self.subTest("basic settings without suffix"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={
                    "app": ["path/to/main_script"],
                },
            )
            self.assertEqual(command.distribution.metadata.name, "main_script")

        with self.subTest("with name"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={
                    "name": "hello",
                    "app": ["script.py"],
                },
            )
            self.assertEqual(command.distribution.metadata.name, "hello")

    def test_default_app_config(self):
        command = self.run_setuptools(
            commandline_options=["setup.py", "py2app2"],
            setup_keywords={
                "app": ["script.py"],
            },
        )

        self.assert_config_types(command.config)
        self.assert_global_options(command.config)
        self.assert_recipe_options(command.config.recipe)
        self.assertEqual(len(command.config.bundles), 1)
        self.assert_bundle_options(
            command.config.bundles[0], plugin=False, script=pathlib.Path("./script.py")
        )

    def test_default_app_config_through_command_line(self):
        command = self.run_setuptools(
            commandline_options=["setup.py", "py2app2", "--app=script.py"],
            setup_keywords={},
        )

        self.assert_config_types(command.config)
        self.assert_global_options(command.config)
        self.assert_recipe_options(command.config.recipe)
        self.assertEqual(len(command.config.bundles), 1)
        self.assert_bundle_options(
            command.config.bundles[0], plugin=False, script=pathlib.Path("./script.py")
        )

    def test_default_plugin_config(self):
        command = self.run_setuptools(
            commandline_options=["setup.py", "py2app2"],
            setup_keywords={
                "plugin": ["script.py"],
            },
        )

        self.assert_config_types(command.config)
        self.assert_global_options(command.config)
        self.assert_recipe_options(command.config.recipe)
        self.assertEqual(len(command.config.bundles), 1)
        self.assert_bundle_options(
            command.config.bundles[0], plugin=True, script=pathlib.Path("./script.py")
        )

    def test_default_plugin_config_through_command_line(self):
        command = self.run_setuptools(
            commandline_options=["setup.py", "py2app2", "--plugin=script.py"],
            setup_keywords={},
        )

        self.assert_config_types(command.config)
        self.assert_global_options(command.config)
        self.assert_recipe_options(command.config.recipe)
        self.assertEqual(len(command.config.bundles), 1)
        self.assert_bundle_options(
            command.config.bundles[0], plugin=True, script=pathlib.Path("./script.py")
        )

    def test_multiple_targets(self):
        for kind in ["app", "plugin"]:
            with self.subTest(f"two {kind} targets"):
                with self.assertRaisesRegex(
                    SystemExit, "error: Multiple targets not currently supported"
                ):
                    self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={
                            kind: ["script.py", "script2.py"],
                        },
                    )

        with self.subTest("app and plugin"):
            with self.assertRaisesRegex(
                SystemExit, "error: You must specify either app or plugin, not both"
            ):
                self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "plugin": ["script2.py"],
                    },
                )

    def test_no_target(self):
        with self.assertRaisesRegex(
            SystemExit, "error: Must specify 'app' or 'plugin'"
        ):
            self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={},
            )

    def test_target_not_list(self):
        for kind in ("app", "plugin"):
            with self.subTest(kind):
                with self.assertRaisesRegex(
                    errors.DistutilsOptionError,
                    "target definition should be a sequence: 42",
                ):

                    self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={kind: 42},
                    )

    def test_target_entry_invalid(self):
        for kind in ("app", "plugin"):
            with self.subTest(kind):
                with self.assertRaisesRegex(
                    errors.DistutilsOptionError, "42 is not a valid target definition"
                ):

                    self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={kind: [42]},
                    )

    def test_target_extra_scripts(self):
        for kind in ["app", "plugin"]:
            with self.subTest(f"{kind} valid definition"):
                command = self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        kind: [
                            {
                                "script": "script.py",
                                "extra_scripts": ["first.py", "second.py"],
                            }
                        ]
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=(kind == "plugin"),
                    script=pathlib.Path("./script.py"),
                    extra_scripts=[
                        pathlib.Path("./first.py"),
                        pathlib.Path("./second.py"),
                    ],
                )

            with self.subTest(f"{kind} non-string entry"):
                with self.assertRaisesRegex(
                    SystemExit, "error: Target 'extra_scripts' is not a list of strings"
                ):
                    command = self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={
                            kind: [
                                {
                                    "script": "script.py",
                                    "extra_scripts": ["first.py", 42],
                                }
                            ]
                        },
                    )

            with self.subTest(f"{kind} not list"):
                with self.assertRaisesRegex(
                    SystemExit, "error: Target 'extra_scripts' is not a list of strings"
                ):
                    command = self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={
                            kind: [
                                {
                                    "script": "script.py",
                                    "extra_scripts": 42,
                                }
                            ]
                        },
                    )

    def test_target_extra_scripts_with_more_in_options(self):
        for kind in ["app", "plugin"]:
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={
                    kind: [
                        {
                            "script": "script.py",
                            "extra_scripts": ["first.py", "second.py"],
                        }
                    ],
                    "options": {
                        "py2app2": {
                            "extra_scripts": ["third.py"],
                        }
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=(kind == "plugin"),
                script=pathlib.Path("./script.py"),
                extra_scripts=[
                    pathlib.Path("./first.py"),
                    pathlib.Path("./second.py"),
                    pathlib.Path("./third.py"),
                ],
            )

    def test_target_extra_keys(self):
        for kind in ("app", "plugin"):
            with self.subTest(kind):
                with self.assertRaisesRegex(
                    errors.DistutilsOptionError, "Invalid key in target definition"
                ):
                    self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={kind: [{"script": "script.py", "unknown": 42}]},
                    )

    def test_option_alias(self):
        with self.subTest("alias in setup.py (true-ish)"):
            for value in (True, 42):
                command = self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "alias": value,
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    build_type=_config.BuildType.ALIAS,
                )

        with self.subTest("alias in setup.py (false-ish)"):
            for value in (False, 0):
                command = self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "alias": value,
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                )

        with self.subTest("alias in setup.py, invalid type"):
            with self.assertRaisesRegex(
                SystemExit, "error: Invalid configuration for 'alias'"
            ):
                self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "alias": 0.5,
                            }
                        },
                    },
                )

        with self.subTest("alias in command-line"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2", "--alias"],
                setup_keywords={
                    "app": ["script.py"],
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                build_type=_config.BuildType.ALIAS,
            )

        with self.subTest("alias and semi-standalone in setup.py"):
            with self.assertRaisesRegex(
                SystemExit, "error: Cannot have both alias and semi-standalone"
            ):
                self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {"alias": True, "semi_standalone": True}
                        },
                    },
                )

    def test_option_semi_standalone(self):
        with self.subTest("semi-standalone in setup.py (true-ish)"):
            for value in (True, 42):
                command = self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "semi_standalone": value,
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    build_type=_config.BuildType.SEMI_STANDALONE,
                )

        with self.subTest("semi-standalone in setup.py (false-ish)"):
            for value in (False, 0):
                command = self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "semi_standalone": value,
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                )

        with self.subTest("semi-standalone in setup.py, invalid type"):
            with self.assertRaisesRegex(
                SystemExit, "error: Invalid configuration for 'semi-standalone'"
            ):
                self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "semi_standalone": 0.5,
                            }
                        },
                    },
                )

        with self.subTest("semi-standalone in command-line"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2", "--semi-standalone"],
                setup_keywords={
                    "app": ["script.py"],
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                build_type=_config.BuildType.SEMI_STANDALONE,
            )

        with self.subTest("alias and semi-standalone in setup.py"):
            with self.assertRaisesRegex(
                SystemExit, "error: Cannot have both alias and semi-standalone"
            ):
                self.run_setuptools(
                    commandline_options=["setup.py", "py2app2", "--alias"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {"py2app2": {"semi_standalone": True}},
                    },
                )

    def test_option_stringlists(self):
        for key, option in [
            ("includes", "py_include"),
            ("excludes", "py_exclude"),
            ("maybe_packages", "py_full_package"),
            ("frameworks", "macho_include"),
            ("dylib_excludes", "macho_exclude"),
        ]:
            with self.subTest(f"{key} through setup.py, valid sequence"):
                command = self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                key: (
                                    "one",
                                    "two",
                                ),
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    **{option: ["one", "two"]},
                )

            with self.subTest(f"{key} through setup.py, valid string"):
                command = self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                key: "one, two",
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    **{option: ["one", "two"]},
                )

            with self.subTest(f"{key} through setup.py, invalid value"):
                with self.assertRaisesRegex(
                    SystemExit, f"error: invalid value for '{key.replace('_', '-')}'"
                ):
                    self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={
                            "app": ["script.py"],
                            "options": {
                                "py2app2": {
                                    key: 42,
                                }
                            },
                        },
                    )

            with self.subTest(f"{key} through setup.py, invalid item"):
                with self.assertRaisesRegex(
                    SystemExit,
                    f"error: invalid value for '{key.replace('_', '-')}': 42 is not a string",
                ):
                    self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={
                            "app": ["script.py"],
                            "options": {
                                "py2app2": {
                                    key: [42],
                                }
                            },
                        },
                    )

            with self.subTest(f"{key} through command-line"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                        f"--{key.replace('_', '-')}=one,two",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    **{option: ["one", "two"]},
                )

    def test_option_packages(self):
        with self.subTest("setup.py, valid sequence"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={
                    "app": ["script.py"],
                    "options": {
                        "py2app2": {
                            "packages": (
                                "one",
                                "two",
                            ),
                            "includes": [
                                "three",
                            ],
                        }
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                py_include=["one", "two", "three"],
                py_full_package=["one", "two"],
            )

        with self.subTest("through setup.py, valid string"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={
                    "app": ["script.py"],
                    "options": {
                        "py2app2": {
                            "packages": "one, two",
                        }
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                py_include=["one", "two"],
                py_full_package=["one", "two"],
            )

        with self.subTest("through setup.py, invalid value"):
            with self.assertRaisesRegex(
                SystemExit, "error: invalid value for 'packages'"
            ):
                self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "packages": 42,
                            }
                        },
                    },
                )

        with self.subTest("through setup.py, invalid item"):
            with self.assertRaisesRegex(
                SystemExit,
                "error: invalid value for 'packages': 42 is not a string",
            ):
                self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "packages": [42],
                            }
                        },
                    },
                )

        with self.subTest("through command-line"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                    "--packages=one,two",
                ],
                setup_keywords={
                    "app": ["script.py"],
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                py_include=["one", "two"],
                py_full_package=["one", "two"],
            )

    def test_option_bool(self):
        for key, option, is_global in [
            ("strip", "macho_strip", True),
            ("chdir", "chdir", False),
            ("emulate_shell_environment", "emulate_shell_environment", False),
            ("redirect_stdout_to_asl", "redirect_to_asl", False),
            ("use_pythonpath", "python_use_pythonpath", False),
            ("site_packages", "python_use_sitepackages", False),
            ("use_faulthandler", "python_use_faulthandler", False),
            ("verbose_interpreter", "python_verbose", False),
            ("argv_emulation", "argv_emulator", False),
        ]:
            for kind in ("app", "plugin"):
                for value in (True, False, 0, 42):
                    with self.subTest(f"{key} through setup.py, {value} in {kind}"):
                        command = self.run_setuptools(
                            commandline_options=["setup.py", "py2app2"],
                            setup_keywords={
                                kind: ["script.py"],
                                "options": {
                                    "py2app2": {
                                        key: value,
                                    }
                                },
                            },
                        )

                        global_options = local_options = {}
                        if is_global:
                            global_options = {option: bool(value)}
                        else:
                            local_options = {option: bool(value)}

                        self.assert_config_types(command.config)
                        self.assert_global_options(command.config, **global_options)
                        self.assert_recipe_options(command.config.recipe)
                        self.assertEqual(len(command.config.bundles), 1)
                        self.assert_bundle_options(
                            command.config.bundles[0],
                            plugin=(kind == "plugin"),
                            script=pathlib.Path("./script.py"),
                            **local_options,
                        )

                with self.subTest(f"{key} through setup.py, 'on' in {kind}"):
                    command = self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={
                            "app": ["script.py"],
                            "options": {
                                "py2app2": {
                                    key: "on",
                                }
                            },
                        },
                    )
                    local_options = global_options = {}
                    if is_global:
                        global_options = {option: True}
                    else:
                        local_options = {option: True}

                    self.assert_config_types(command.config)
                    self.assert_global_options(command.config, **global_options)
                    self.assert_recipe_options(command.config.recipe)
                    self.assertEqual(len(command.config.bundles), 1)
                    self.assert_bundle_options(
                        command.config.bundles[0],
                        plugin=False,
                        script=pathlib.Path("./script.py"),
                        **local_options,
                    )

                with self.subTest(f"{key} through setup.py, 'off' in {kind}"):
                    command = self.run_setuptools(
                        commandline_options=["setup.py", "py2app2"],
                        setup_keywords={
                            "app": ["script.py"],
                            "options": {
                                "py2app2": {
                                    key: "off",
                                }
                            },
                        },
                    )

                    local_options = global_options = {}
                    if is_global:
                        global_options = {option: False}
                    else:
                        local_options = {option: False}

                    self.assert_config_types(command.config)
                    self.assert_global_options(command.config, **global_options)
                    self.assert_recipe_options(command.config.recipe)
                    self.assertEqual(len(command.config.bundles), 1)
                    self.assert_bundle_options(
                        command.config.bundles[0],
                        plugin=False,
                        script=pathlib.Path("./script.py"),
                        **local_options,
                    )

                with self.subTest(f"{key} through setup.py, invalid value in {kind}"):
                    with self.assertRaisesRegex(
                        SystemExit, "error: invalid truth value 'bla bla'"
                    ):
                        self.run_setuptools(
                            commandline_options=["setup.py", "py2app2"],
                            setup_keywords={
                                "app": ["script.py"],
                                "options": {
                                    "py2app2": {
                                        key: "bla bla",
                                    }
                                },
                            },
                        )

                with self.subTest(f"{key} through command-line (on) in {kind}"):
                    command = self.run_setuptools(
                        commandline_options=[
                            "setup.py",
                            "py2app2",
                            f"--{key.replace('_', '-')}",
                        ],
                        setup_keywords={
                            "app": ["script.py"],
                        },
                    )

                    local_options = global_options = {}
                    if is_global:
                        global_options = {option: True}
                    else:
                        local_options = {option: True}

                    self.assert_config_types(command.config)
                    self.assert_global_options(command.config, **global_options)
                    self.assert_recipe_options(command.config.recipe)
                    self.assertEqual(len(command.config.bundles), 1)
                    self.assert_bundle_options(
                        command.config.bundles[0],
                        plugin=False,
                        script=pathlib.Path("./script.py"),
                        **local_options,
                    )

                with self.subTest(f"{key} through command-line (off) in {kind}"):
                    command = self.run_setuptools(
                        commandline_options=[
                            "setup.py",
                            "py2app2",
                            f"--no-{key.replace('_', '-')}",
                        ],
                        setup_keywords={
                            "app": ["script.py"],
                        },
                    )

                    local_options = global_options = {}
                    if is_global:
                        global_options = {option: False}
                    else:
                        local_options = {option: False}

                    self.assert_config_types(command.config)
                    self.assert_global_options(command.config, **global_options)
                    self.assert_recipe_options(command.config.recipe)
                    self.assertEqual(len(command.config.bundles), 1)
                    self.assert_bundle_options(
                        command.config.bundles[0],
                        plugin=False,
                        script=pathlib.Path("./script.py"),
                        **local_options,
                    )

    def test_option_plist(self):
        with self.subTest("valid dict in setup.py"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                ],
                setup_keywords={
                    "app": ["script.py"],
                    "options": {"py2app2": {"plist": {"foo": "bar"}}},
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                plist={"foo": "bar"},
            )

        with self.subTest("invalid value in setup.py"):
            with self.assertRaisesRegex(SystemExit, "error: Invalid value for 'plist'"):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {"py2app2": {"plist": 42}},
                    },
                )

        with self.subTest("value not serializable in setup.py"):
            with self.assertRaisesRegex(
                SystemExit, "error: Cannot serialize 'plist' value"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {"py2app2": {"plist": {42: "ok"}}},
                    },
                )

        with self.subTest("correct plist file in setup.py"):
            data = plistlib.dumps({"key": "value"}, fmt=plistlib.FMT_BINARY)
            stream = io.BytesIO(data)

            with mock.patch(
                "py2app._setuptools_stub.open", return_value=stream
            ) as mock_open:
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {"py2app2": {"plist": "./data/Info.plist"}},
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    plist={"key": "value"},
                )
            mock_open.assert_called_once_with("./data/Info.plist", "rb")

        with self.subTest("missing plist file in setup.py"):
            with self.assertRaisesRegex(
                SystemExit, "error: Cannot open plist file 'no-such-file.plist'"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {"py2app2": {"plist": "no-such-file.plist"}},
                    },
                )

        with self.subTest("incorrect plist file in setup.py"):
            data = b"invalid data"
            stream = io.BytesIO(data)

            with self.assertRaisesRegex(
                SystemExit, "error: Invalid plist file './data/Info.plist'"
            ):
                with mock.patch(
                    "py2app._setuptools_stub.open", return_value=stream
                ) as mock_open:
                    self.run_setuptools(
                        commandline_options=[
                            "setup.py",
                            "py2app2",
                        ],
                        setup_keywords={
                            "app": ["script.py"],
                            "options": {"py2app2": {"plist": "./data/Info.plist"}},
                        },
                    )
            mock_open.assert_called_once_with("./data/Info.plist", "rb")

        with self.subTest("valid plist file through command-line"):
            data = plistlib.dumps({"key": "value"}, fmt=plistlib.FMT_BINARY)
            stream = io.BytesIO(data)

            with mock.patch(
                "py2app._setuptools_stub.open", return_value=stream
            ) as mock_open:
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                        "--plist=./data/Info.plist",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    plist={"key": "value"},
                )
            mock_open.assert_called_once_with("./data/Info.plist", "rb")

        with self.subTest("missing plist file through command-line"):
            with self.assertRaisesRegex(
                SystemExit, "error: Cannot open plist file 'no-such-file.plist'"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                        "--plist=no-such-file.plist",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                    },
                )

        with self.subTest("invalid plist file through command-line"):
            data = b"invalid data"
            stream = io.BytesIO(data)

            with self.assertRaisesRegex(
                SystemExit, "error: Invalid plist file './data/Info.plist'"
            ):
                with mock.patch(
                    "py2app._setuptools_stub.open", return_value=stream
                ) as mock_open:
                    self.run_setuptools(
                        commandline_options=[
                            "setup.py",
                            "py2app2",
                            "--plist=./data/Info.plist",
                        ],
                        setup_keywords={
                            "app": ["script.py"],
                        },
                    )
            mock_open.assert_called_once_with("./data/Info.plist", "rb")

    def test_option_iconfile(self):
        with self.subTest("value in setup.py"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                ],
                setup_keywords={
                    "app": ["script.py"],
                    "options": {
                        "py2app2": {
                            "iconfile": "path/to/icon.icns",
                        }
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                iconfile=pathlib.Path("./path/to/icon.icns"),
            )

        with self.subTest("invalid value in setup.py"):
            with self.assertRaisesRegex(
                SystemExit, "error: Invalid value for 'iconfile'"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "iconfile": 12,
                            }
                        },
                    },
                )

        with self.subTest("value in command-line"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                    "--iconfile=path/to/icon.icns",
                ],
                setup_keywords={
                    "app": ["script.py"],
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                iconfile=pathlib.Path("./path/to/icon.icns"),
            )

    def test_option_extension(self):
        for plugin in (True, False):
            with self.subTest(f"value in setup.py, {plugin}"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "plugin" if plugin else "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "extension": ".foo",
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=plugin,
                    script=pathlib.Path("./script.py"),
                    extension=".foo",
                )

        with self.subTest("invalid value in setup.py"):
            with self.assertRaisesRegex(
                SystemExit, "error: Invalid configuration for 'extension'"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "extension": 12,
                            }
                        },
                    },
                )

        with self.subTest("value in command-line"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                    "--extension=.mdindex",
                ],
                setup_keywords={
                    "app": ["script.py"],
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                extension=".mdindex",
            )

    def test_option_optimize(self):
        for value in (0, 1, 42, True, False):
            with self.subTest(f"value in setup.py, {value!r}"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "options": {
                            "py2app2": {
                                "app": ["script.py"],
                                "optimize": value,
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    script=pathlib.Path("./script.py"),
                    python_optimize=int(value),
                )

        with self.subTest("invalid value in setup.py, float"):
            with self.assertRaisesRegex(
                SystemExit, "error: Invalid value for 'optimize'"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "optimize": 1.5,
                            }
                        },
                    },
                )

        with self.subTest("invalid value in setup.py, string"):
            with self.assertRaisesRegex(
                SystemExit, "error: Invalid value for 'optimize'"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {"py2app2": {"optimize": "off"}},
                    },
                )

        with self.subTest("value in command-line"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                    "--optimize=2",
                ],
                setup_keywords={
                    "app": ["script.py"],
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                python_optimize=2,
            )

    def test_option_resources(self):
        pwd = pathlib.Path(".")

        for key in ("resources", "datamodels", "mappingmodels"):
            with self.subTest(f"simple list for {key} in setup.py"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                key: ["a", "b"],
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)

                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    resources=[
                        _config.Resource(pwd, [pwd / "a"]),
                        _config.Resource(pwd, [pwd / "b"]),
                    ],
                )

            with self.subTest(f"string value for {key} in setup.py"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                key: "a,b",
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)

                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    resources=[
                        _config.Resource(pwd, [pwd / "a"]),
                        _config.Resource(pwd, [pwd / "b"]),
                    ],
                )

            with self.subTest(f"complex value for {key} in setup.py"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                key: ["a", ("b", ["c", "d"])],
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)

                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    resources=[
                        _config.Resource(pwd, [pwd / "a"]),
                        _config.Resource(pathlib.Path("b"), [pwd / "c", pwd / "d"]),
                    ],
                )

            with self.subTest(f"invalid value for {key} in setup.py"):
                with self.assertRaisesRegex(
                    SystemExit, f"error: invalid value for '{key}'"
                ):
                    self.run_setuptools(
                        commandline_options=[
                            "setup.py",
                            "py2app2",
                        ],
                        setup_keywords={
                            "app": ["script.py"],
                            "options": {
                                "py2app2": {
                                    key: 42,
                                }
                            },
                        },
                    )

            with self.subTest(f"invalid value for {key} in setup.py"):
                with self.assertRaisesRegex(
                    SystemExit, f"error: invalid value for '{key}'"
                ):
                    self.run_setuptools(
                        commandline_options=[
                            "setup.py",
                            "py2app2",
                        ],
                        setup_keywords={
                            "app": ["script.py"],
                            "options": {
                                "py2app2": {
                                    key: [42],
                                }
                            },
                        },
                    )

        with self.subTest("specify all"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                    "--datamodels=model.dm",
                ],
                setup_keywords={
                    "app": ["script.py"],
                    "options": {
                        "py2app2": {
                            "resources": ["resource.txt"],
                            "mappingmodels": "mapping.model",
                        },
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)

            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                resources=[
                    _config.Resource(pwd, [pathlib.Path("./resource.txt")]),
                    _config.Resource(pwd, [pathlib.Path("./mapping.model")]),
                    _config.Resource(pwd, [pathlib.Path("./model.dm")]),
                ],
            )

            self.assertEqual(
                command.warnings,
                [
                    "WARNING: the datamodels option is deprecated, add model files to the list of resources",
                    "WARNING: the mappingmodels option is deprecated, add model files to the list of resources",
                ],
            )

    def test_option_extra_scripts(self):
        with self.subTest("through setup.py, valid sequence"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={
                    "app": ["script.py"],
                    "options": {
                        "py2app2": {
                            "extra_scripts": (
                                "one",
                                "two",
                            ),
                        }
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                extra_scripts=[pathlib.Path("./one"), pathlib.Path("./two")],
            )

        with self.subTest("through setup.py, valid string"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={
                    "app": ["script.py"],
                    "options": {
                        "py2app2": {
                            "extra_scripts": "one, two",
                        }
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                extra_scripts=[pathlib.Path("./one"), pathlib.Path("./two")],
            )

        with self.subTest("through setup.py, invalid value"):
            with self.assertRaisesRegex(
                SystemExit, "error: invalid value for 'extra-scripts'"
            ):
                self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "extra_scripts": 42,
                            }
                        },
                    },
                )

        with self.subTest("through setup.py, invalid item"):
            with self.assertRaisesRegex(
                SystemExit,
                "error: invalid value for 'extra-scripts': 42 is not a string",
            ):
                self.run_setuptools(
                    commandline_options=["setup.py", "py2app2"],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "extra_scripts": [42],
                            }
                        },
                    },
                )

        with self.subTest("through command-line"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                    "--extra-scripts=one,two",
                ],
                setup_keywords={
                    "app": ["script.py"],
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                extra_scripts=[pathlib.Path("./one"), pathlib.Path("./two")],
            )

        with self.subTest("through setup.py with target, valid sequence"):
            command = self.run_setuptools(
                commandline_options=["setup.py", "py2app2"],
                setup_keywords={
                    "app": [{"script": "script.py", "extra_scripts": ["three"]}],
                    "options": {
                        "py2app2": {
                            "extra_scripts": (
                                "one",
                                "two",
                            ),
                        }
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                extra_scripts=[
                    pathlib.Path("./one"),
                    pathlib.Path("./two"),
                    pathlib.Path("./three"),
                ],
            )

    def test_option_argv_inject(self):
        with self.subTest("value as tuple of strings"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                ],
                setup_keywords={
                    "app": ["script.py"],
                    "options": {
                        "py2app2": {
                            "argv_inject": ("a", "b"),
                        }
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                argv_inject=["a", "b"],
            )

        with self.subTest("value as string"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                ],
                setup_keywords={
                    "app": ["script.py"],
                    "options": {
                        "py2app2": {
                            "argv_inject": "foo 'bar, baz'",
                        }
                    },
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                argv_inject=["foo", "bar, baz"],
            )

        with self.subTest("value not shlex parsable"):
            with self.assertRaisesRegex(
                SystemExit, "error: Invalid configuration for 'argv-inject'"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "argv_inject": "foo ' bar",
                            }
                        },
                    },
                )

        with self.subTest("value as integer"):
            with self.assertRaisesRegex(
                SystemExit, "error: Invalid configuration for 'argv-inject'"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "argv_inject": 42,
                            }
                        },
                    },
                )

        with self.subTest("value as list of int"):
            with self.assertRaisesRegex(
                SystemExit, "Invalid configuration for 'argv-inject'"
            ):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "argv_inject": [42],
                            }
                        },
                    },
                )

        with self.subTest("value in command-line"):
            command = self.run_setuptools(
                commandline_options=[
                    "setup.py",
                    "py2app2",
                    "--argv-inject=foo 'bar, baz'",
                ],
                setup_keywords={
                    "app": ["script.py"],
                },
            )

            self.assert_config_types(command.config)
            self.assert_global_options(command.config)
            self.assert_recipe_options(command.config.recipe)
            self.assertEqual(len(command.config.bundles), 1)
            self.assert_bundle_options(
                command.config.bundles[0],
                plugin=False,
                script=pathlib.Path("./script.py"),
                argv_inject=["foo", "bar, baz"],
            )

    def test_option_arch(self):
        for value in ("x86_64", "arm64", "universal2"):
            with self.subTest(f"value in setup.py, {value!r}"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "options": {
                            "py2app2": {
                                "app": ["script.py"],
                                "arch": value,
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    script=pathlib.Path("./script.py"),
                    macho_arch=_config.BuildArch(value),
                )

        with self.subTest("invalid value in setup.py, float"):
            with self.assertRaisesRegex(SystemExit, "error: Invalid value for 'arch'"):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {
                            "py2app2": {
                                "arch": 1.5,
                            }
                        },
                    },
                )

        with self.subTest("invalid value in setup.py, string"):
            with self.assertRaisesRegex(SystemExit, "error: Invalid value for 'arch'"):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                        "options": {"py2app2": {"arch": "ppc"}},
                    },
                )

        for value in ("x86_64", "arm64", "universal2"):
            with self.subTest(f"value in command-line, {value}"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                        f"--arch={value}",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(command.config.recipe)
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    plugin=False,
                    script=pathlib.Path("./script.py"),
                    macho_arch=_config.BuildArch(value),
                )

        with self.subTest("invalid value in command-line"):
            with self.assertRaisesRegex(SystemExit, "error: Invalid value for 'arch'"):
                self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                        "--arch=ppc",
                    ],
                    setup_keywords={
                        "app": ["script.py"],
                    },
                )

    def test_option_recipe_options(self):
        for option, attribute in [
            ("qt_plugins", "qt_plugins"),
            ("matplotlib_backends", "matplotlib_backends"),
        ]:
            with self.subTest("valid string list in setup.py"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                    ],
                    setup_keywords={
                        "options": {
                            "py2app2": {
                                "app": ["script.py"],
                                option: ["a", "b"],
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(
                    command.config.recipe, **{attribute: ["a", "b"]}
                )
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    script=pathlib.Path("./script.py"),
                )

            with self.subTest("invalid list item in setup.py"):
                with self.assertRaisesRegex(
                    SystemExit,
                    f"error: invalid value for '{option.replace('_', '-')}': 42 is not a string",
                ):
                    self.run_setuptools(
                        commandline_options=[
                            "setup.py",
                            "py2app2",
                        ],
                        setup_keywords={
                            "app": ["script.py"],
                            "options": {"py2app2": {option: [42]}},
                        },
                    )

            with self.subTest("invalid value in setup.py"):
                with self.assertRaisesRegex(
                    SystemExit, f"error: invalid value for '{option.replace('_', '-')}'"
                ):
                    self.run_setuptools(
                        commandline_options=[
                            "setup.py",
                            "py2app2",
                        ],
                        setup_keywords={
                            "app": ["script.py"],
                            "options": {"py2app2": {option: 42}},
                        },
                    )

            with self.subTest("value though command-line"):
                command = self.run_setuptools(
                    commandline_options=[
                        "setup.py",
                        "py2app2",
                        f"--{option.replace('_', '-')}=a,b",
                    ],
                    setup_keywords={
                        "options": {
                            "py2app2": {
                                "app": ["script.py"],
                            }
                        },
                    },
                )

                self.assert_config_types(command.config)
                self.assert_global_options(command.config)
                self.assert_recipe_options(
                    command.config.recipe, **{attribute: ["a", "b"]}
                )
                self.assertEqual(len(command.config.bundles), 1)
                self.assert_bundle_options(
                    command.config.bundles[0],
                    script=pathlib.Path("./script.py"),
                )


# XXX: These options have not yet been been ported to the new
#      setuptools command:
# XXX: test_target_build_directory
# XXX: test_target_prescripts (?)
"""
    user_options = [
    # Reporting options:
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
            "expected-missing-imports=",
            None,
            "expected missing imports either a comma sperated list "
            "or @ followed by file containing a list of imports, one per line",
        ),
    ]

    # setuptools bdist options (also: dry-run)

        ("bdist-base=", "b", "base directory for build library (default is build)"),
        (
            "dist-dir=",
            "d",
            "directory to put final built distributions in (default is dist)",
        ),

    # Not ready yet:
        ("include-plugins=", None, "List of plugins to include"),

    # Specials::
        ("graph", "g", "output module dependency graph"),
        ("xref", "x", "output module cross-reference as html"),
    """


class TestSetuptoolsRunning(TestCase):
    # XXX
    # This should contain a small number of test cases:
    # - mock "builder" with valid and invalid invocation,
    #   check how builder is invoked
    # - real builder with trivial configuration (integration
    #   test). Possibly second test case with warnings

    pass
