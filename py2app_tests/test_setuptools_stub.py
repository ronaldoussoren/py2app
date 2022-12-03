import pathlib
import plistlib
import sys
from unittest import TestCase, mock

import setuptools

from py2app import _config

NOT_SET = object()


class TestSetuptoolsConfiguration(TestCase):
    # This class tests the argument parsing of
    # the setuptools compatibility stub.

    # XXX:
    # - set options though command-line
    # - set options though setup(options={"py2app":..})
    # - target options (including additional options)
    #

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

        self.assertIsInstance(config.recipe.matplotlib_plugins, list)
        self.assertTrue(
            all(isinstance(item, str) for item in config.recipe.matplotlib_plugins)
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
        self.assertTrue(all(isinstance(item, str) for item in bundle.resources))
        self.assertIsInstance(bundle.plist, dict)
        plistlib.dumps(bundle.plist)
        self.assertIsInstance(bundle.extra_scripts, list)
        self.assertTrue(
            all(isinstance(item, pathlib.Path) for item in bundle.extra_scripts)
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
        self, options, *, zip_unsafe=(), qt_plugins=(), matplotlib_plugins=()
    ):
        self.assertIsInstance(options, _config.RecipeOptions)
        self.assertIsInstance(options.zip_unsafe, list)
        self.assertIsInstance(options.qt_plugins, list)
        self.assertIsInstance(options.matplotlib_plugins, list)

        self.assertCountEqual(options.zip_unsafe, zip_unsafe)
        self.assertCountEqual(options.qt_plugins, qt_plugins)
        self.assertCountEqual(options.matplotlib_plugins, matplotlib_plugins)

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
            self.assertNotIn("stip", options._local)
        else:
            self.assertIn("stip", options._local)
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

    # test_target_extra_scripts (for kind in app, plugin)
