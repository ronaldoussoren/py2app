# XXX: It should be possible to simplicy these tests.
import io
import pathlib
import plistlib
import sys
import sysconfig
from unittest import TestCase, mock

from py2app import _config


class TestPropertyHelpers(TestCase):
    def test_local(self):
        class Holder:
            is_set = _config.local[bool]("is_set", False)
            path = _config.local[str]("path-value")

        value = Holder()
        value._local = {}

        self.assertEqual(value.is_set, False)
        with self.assertRaisesRegex(AttributeError, "path-value"):
            value.path

        value._local["is_set"] = True
        value._local["path-value"] = "hello"

        self.assertEqual(value.is_set, True)
        self.assertEqual(value.path, "hello")

    def test_inherited(self):
        class Bag:
            first_value: int
            second: int

        class Holder:
            first = _config.inherited[int]("first-value", "first_value")
            second = _config.inherited[int]("second", "second")

        bag = Bag()
        value = Holder()
        value._global = bag
        value._local = {}

        with self.assertRaisesRegex(AttributeError, "first_value"):
            value.first

        with self.assertRaisesRegex(AttributeError, "second"):
            value.second

        bag.first_value = 42
        self.assertEqual(value.first, 42)

        bag.second = 2
        self.assertEqual(value.second, 2)

        value._local["first-value"] = 99
        value._local["second"] = 4

        self.assertEqual(value.first, 99)
        self.assertEqual(value.second, 4)


class TestResource(TestCase):
    def test_from_single(self):
        root = pathlib.Path("etc")
        value = _config.Resource.from_config("value", root, "my_location")
        self.assertIsInstance(value, _config.Resource)
        self.assertEqual(value.destination, pathlib.Path("."))
        self.assertEqual(value.sources, [root / "value"])

    def test_from_item(self):
        root = pathlib.Path("etc")
        value = _config.Resource.from_config(
            ["dir", ["file1", "file2"]], root, "my_location"
        )
        self.assertIsInstance(value, _config.Resource)
        self.assertEqual(value.destination, pathlib.Path("dir"))
        self.assertEqual(value.sources, [root / "file1", root / "file2"])

    def test_from_invalid_item(self):
        root = pathlib.Path("etc")
        with self.assertRaisesRegex(
            _config.ConfigurationError,
            r"my_location: invalid item \['one', 'two', 'three']",
        ):
            _config.Resource.from_config(["one", "two", "three"], root, "my_location")

        with self.assertRaisesRegex(
            _config.ConfigurationError,
            r"my_location: invalid item \['one', \[2, 'three']]",
        ):
            _config.Resource.from_config(["one", [2, "three"]], root, "my_location")

        with self.assertRaisesRegex(
            _config.ConfigurationError,
            r"my_location: invalid item \[1, \['two', 'three']]",
        ):
            _config.Resource.from_config([1, ["two", "three"]], root, "my_location")

    def test_from_invalid_value(self):
        root = pathlib.Path("etc")
        with self.assertRaisesRegex(
            _config.ConfigurationError, "my_location: invalid item 42"
        ):
            _config.Resource.from_config(42, root, "my_location")


class TestParsing(TestCase):
    # XXX: This indirectly also tests the various option
    #      classes. Also add direct tests!
    def test_missing(self):
        with self.assertRaisesRegex(
            _config.ConfigurationError,
            "Configuration doesn't contain a 'tool.py2app' key",
        ):
            _config.parse_pyproject({}, pathlib.Path("."))

        with self.assertRaisesRegex(
            _config.ConfigurationError,
            "Configuration doesn't contain a 'tool.py2app' key",
        ):
            _config.parse_pyproject({"tool": {"setuptools": {}}}, pathlib.Path("."))

    def test_recipe_configuration(self):
        with self.subTest("default configuration"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                }
                            }
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.recipe.zip_unsafe, [])
            self.assertEqual(config.recipe.qt_plugins, None)
            self.assertEqual(config.recipe.matplotlib_plugins, None)

        with self.subTest("invalid main key"):
            with self.assertRaisesRegex(
                _config.ConfigurationError, "'tool.py2app.recipe' is not a dictionary"
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "recipe": 42,
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("invalid subkey"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.recipe.spam' is not a valid key",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "recipe": {
                                    "spam": 42,
                                },
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        for subkey, attribute in [
            ("zip-unsafe", "zip_unsafe"),
            ("qt-plugins", "qt_plugins"),
            ("matplotlib-plugins", "matplotlib_plugins"),
        ]:
            with self.subTest(f"setting {subkey} (valid)"):
                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "recipe": {
                                    subkey: ["a", "b", "c"],
                                },
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(getattr(config.recipe, attribute), ["a", "b", "c"])

            with self.subTest(f"setting {subkey} (invalid)"):
                with self.assertRaisesRegex(
                    _config.ConfigurationError,
                    f"'tool.py2app.recipe.{subkey}' is not a list of strings",
                ):
                    _config.parse_pyproject(
                        {
                            "tool": {
                                "py2app": {
                                    "recipe": {
                                        subkey: 44,
                                    },
                                    "bundle": {
                                        "main": {
                                            "script": "main.py",
                                        }
                                    },
                                }
                            }
                        },
                        pathlib.Path("."),
                    )

                with self.assertRaisesRegex(
                    _config.ConfigurationError,
                    f"'tool.py2app.recipe.{subkey}' is not a list of strings",
                ):
                    _config.parse_pyproject(
                        {
                            "tool": {
                                "py2app": {
                                    "recipe": {subkey: [42]},
                                    "bundle": {
                                        "main": {
                                            "script": "main.py",
                                        }
                                    },
                                }
                            }
                        },
                        pathlib.Path("."),
                    )

    def test_global_options(self):
        with self.subTest("default configuration"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                }
                            }
                        }
                    }
                },
                pathlib.Path("."),
            )

            platform = sysconfig.get_platform()
            osname, osrelease, cpuarch = platform.split("-")

            self.assertEqual(config.build_type, _config.BuildType.STANDALONE)
            self.assertEqual(config.deployment_target, osrelease)
            self.assertEqual(config.macho_strip, True)
            self.assertEqual(config.macho_arch, cpuarch)
            self.assertEqual(config.python_optimize, sys.flags.optimize)
            self.assertEqual(config.python_verbose, bool(sys.flags.verbose))
            self.assertEqual(config.python_use_pythonpath, False)
            self.assertEqual(config.python_use_sitepackages, False)
            self.assertEqual(config.python_use_faulthandler, False)

            self.assertEqual(config.bundles[0].build_type, _config.BuildType.STANDALONE)
            self.assertEqual(config.bundles[0].deployment_target, osrelease)
            self.assertEqual(config.bundles[0].macho_strip, True)
            self.assertEqual(config.bundles[0].macho_arch, cpuarch)
            self.assertEqual(config.bundles[0].python_optimize, sys.flags.optimize)
            self.assertEqual(config.bundles[0].python_verbose, bool(sys.flags.verbose))
            self.assertEqual(config.bundles[0].python_use_pythonpath, False)
            self.assertEqual(config.bundles[0].python_use_sitepackages, False)
            self.assertEqual(config.bundles[0].python_use_faulthandler, False)

        with self.subTest("deployment-target (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "deployment-target": "10.1",
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.deployment_target, "10.1")

            self.assertEqual(config.bundles[0].deployment_target, "10.1")

            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "deployment-target": "13",
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )

            self.assertEqual(config.deployment_target, "13")

            self.assertEqual(config.bundles[0].deployment_target, "13")

        with self.subTest("deployment-target (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.deployment-target' is not valid",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "deployment-target": 42,
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.deployment-target' is not valid",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "deployment-target": "catalina",
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.deployment-target' is not valid",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "deployment-target": "10.15.3",
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.deployment-target' is not valid",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "deployment-target": "10_15",
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("strip (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "strip": True,
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.macho_strip, True)
            self.assertEqual(config.bundles[0].macho_strip, True)

            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "strip": False,
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.macho_strip, False)
            self.assertEqual(config.bundles[0].macho_strip, False)

        with self.subTest("strip (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError, "'tool.py2app.strip' is not a boolean"
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "strip": "off",
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("build-type (valid)"):
            for value in ("standalone", "semi-standalone", "alias"):
                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "build-type": value,
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(config.build_type, _config.BuildType(value))
                self.assertEqual(config.bundles[0].build_type, _config.BuildType(value))

        with self.subTest("build-type (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError, "'tool.py2app.build-type' has invalid value"
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "build-type": "off",
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("arch (valid)"):
            for value in ("x86_64", "arm64", "universal2"):
                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "arch": value,
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(config.macho_arch, value)
                self.assertEqual(config.bundles[0].macho_arch, value)

        with self.subTest("arch (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError, "'tool.py2app.arch' has invalid value"
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "arch": "off",
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("python.optimize (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "python": {
                                "optimize": 42,
                            },
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.python_optimize, 42)
            self.assertEqual(config.bundles[0].python_optimize, 42)

        with self.subTest("python.optimize (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.python.optimize' is not an integer",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "python": {
                                    "optimize": "off",
                                },
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        for subkey, attribute in [
            ("verbose", "python_verbose"),
            ("use-pythonpath", "python_use_pythonpath"),
            ("use-sitepackages", "python_use_sitepackages"),
            ("use-faulthandler", "python_use_faulthandler"),
        ]:
            with self.subTest(f"setting python.{subkey} (valid)"):
                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "python": {subkey: True},
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(getattr(config, attribute), True)
                self.assertEqual(getattr(config.bundles[0], attribute), True)

                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "python": {subkey: False},
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(getattr(config, attribute), False)
                self.assertEqual(getattr(config.bundles[0], attribute), False)

            with self.subTest(f"setting {subkey} (invalid)"):
                with self.assertRaisesRegex(
                    _config.ConfigurationError,
                    f"'tool.py2app.python.{subkey}' is not a boolean",
                ):
                    _config.parse_pyproject(
                        {
                            "tool": {
                                "py2app": {
                                    "python": {
                                        subkey: "hello",
                                    },
                                    "bundle": {
                                        "main": {
                                            "script": "main.py",
                                        }
                                    },
                                }
                            }
                        },
                        pathlib.Path("."),
                    )

        with self.subTest("invalid python key"):
            with self.assertRaisesRegex(
                _config.ConfigurationError, "'tool.py2app.python' is not a dictionary"
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "python": 42,
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("invalid key"):
            with self.assertRaisesRegex(
                _config.ConfigurationError, "invalid key 'tool.py2app.foo'"
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "foo": 42,
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

    def test_bundle_options(self):
        with self.subTest("missing bundles"):
            with self.assertRaisesRegex(
                _config.ConfigurationError, "missing key: 'tool.py2app.bundle'"
            ):
                _config.parse_pyproject({"tool": {"py2app": {}}}, pathlib.Path("."))

        with self.subTest("invalid type for bundle"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle' is not a sequence of dicts",
            ):
                _config.parse_pyproject(
                    {"tool": {"py2app": {"bundle": 42}}}, pathlib.Path(".")
                )

            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle' is not a sequence of dicts",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "name": {},
                                    "name2": 4,
                                }
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("missing script"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "missing 'script' in 'tool.py2app.bundle.test'",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {"test": {}},
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("script (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].script, pathlib.Path("scriptmod.py"))
            self.assertEqual(config.bundles[0].name, "scriptmod")

        with self.subTest("script (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.script' is not a string",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": 42,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("name (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "name": "Hello World",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].script, pathlib.Path("scriptmod.py"))
            self.assertEqual(config.bundles[0].name, "Hello World")

        with self.subTest("name (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.name' is not a string",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "scriptmod.py",
                                        "name": 42,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("iconfile (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "iconfile": "hello.icns",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].script, pathlib.Path("scriptmod.py"))
            self.assertEqual(config.bundles[0].iconfile, pathlib.Path("hello.icns"))

        with self.subTest("iconfile (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.iconfile' is not a string",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "scriptmod.py",
                                        "iconfile": 42,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        for subkey, attribute in [
            ("plugin", "plugin"),
            ("chdir", "chdir"),
            ("argv-emulator", "argv_emulator"),
            ("emulate-shell-environment", "emulate_shell_environment"),
            ("redirect-to-asl", "redirect_to_asl"),
        ]:
            with self.subTest(f"{subkey} (valid)"):
                for value in (True, False):
                    config = _config.parse_pyproject(
                        {
                            "tool": {
                                "py2app": {
                                    "bundle": {
                                        "test": {
                                            "script": "scriptmod.py",
                                            subkey: value,
                                        }
                                    },
                                }
                            }
                        },
                        pathlib.Path("."),
                    )
                    self.assertEqual(getattr(config.bundles[0], attribute), value)

            with self.subTest(f"{subkey} (invalid)"):
                with self.assertRaisesRegex(
                    _config.ConfigurationError,
                    f"'tool.py2app.bundle.test.{subkey}' is not a boolean",
                ):
                    _config.parse_pyproject(
                        {
                            "tool": {
                                "py2app": {
                                    "bundle": {
                                        "test": {
                                            "script": "main.py",
                                            subkey: "off",
                                        }
                                    },
                                }
                            }
                        },
                        pathlib.Path("."),
                    )

        with self.subTest("extension/chdir (default)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "plugin": True,
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].plugin, True)
            self.assertEqual(config.bundles[0].extension, ".plugin")
            self.assertEqual(config.bundles[0].chdir, False)

            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "plugin": False,
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].plugin, False)
            self.assertEqual(config.bundles[0].extension, ".app")
            self.assertEqual(config.bundles[0].chdir, True)

            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].plugin, False)
            self.assertEqual(config.bundles[0].extension, ".app")
            self.assertEqual(config.bundles[0].chdir, True)

        with self.subTest("extension (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "extension": ".qlplugin",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].extension, ".qlplugin")

        with self.subTest("extension (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.extension' is not a string",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "main.py",
                                        "extension": 42,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        for subkey, attribute in [
            ("include", "py_include"),
            ("exclude", "py_exclude"),
            ("full-package", "py_full_package"),
            ("dylib-include", "macho_include"),
            ("dylib-exclude", "macho_exclude"),
            ("argv-inject", "argv_inject"),
        ]:
            with self.subTest(f"{subkey} (valid)"):
                value = ["x", "y", "z"]
                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "scriptmod.py",
                                        subkey: value,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(getattr(config.bundles[0], attribute), value)

            with self.subTest(f"{subkey} (invalid)"):
                with self.assertRaisesRegex(
                    _config.ConfigurationError,
                    f"'tool.py2app.bundle.test.{subkey}' is not a list of string",
                ):
                    _config.parse_pyproject(
                        {
                            "tool": {
                                "py2app": {
                                    "bundle": {
                                        "test": {
                                            "script": "main.py",
                                            subkey: "off",
                                        }
                                    },
                                }
                            }
                        },
                        pathlib.Path("."),
                    )

                with self.assertRaisesRegex(
                    _config.ConfigurationError,
                    f"'tool.py2app.bundle.test.{subkey}' is not a list of string",
                ):
                    _config.parse_pyproject(
                        {
                            "tool": {
                                "py2app": {
                                    "bundle": {
                                        "test": {
                                            "script": "main.py",
                                            subkey: ["x", 2, "z"],
                                        }
                                    },
                                }
                            }
                        },
                        pathlib.Path("."),
                    )

        with self.subTest("extra-scripts (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "extra-scripts": ["a", "b"],
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(
                config.bundles[0].extra_scripts, [pathlib.Path("a"), pathlib.Path("b")]
            )

        with self.subTest("extra-scripts (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.extra-scripts' is not a list of string",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "main.py",
                                        "extra-scripts": "off",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.extra-scripts' is not a list of string",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "main.py",
                                        "extra-scripts": ["x", 2, "z"],
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("plist (valid, dict)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "plist": {"key": "value"},
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].plist, {"key": "value"})

        with self.subTest("plist (valid, path to existing file)"):
            data = plistlib.dumps({"key": "value"}, fmt=plistlib.FMT_BINARY)
            stream = io.BytesIO(data)

            with mock.patch("py2app._config.open", return_value=stream) as mock_open:
                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "scriptmod.py",
                                        "plist": "data/Info.plist",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(config.bundles[0].plist, {"key": "value"})
            mock_open.assert_called_once_with(pathlib.Path("./data/Info.plist"), "rb")

        with self.subTest("plist (invalid value type)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.plist' is not a dict",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "main.py",
                                        "plist": 42,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("plist (invalid dict structure)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.plist' invalid plist contents",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "main.py",
                                        "plist": {42: 4},
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("plist (non-existing file)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.plist' cannot open 'no/such/file.plist'",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "main.py",
                                        "plist": "no/such/file.plist",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("resources (simple list)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "resources": ["file"],
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(
                config.bundles[0].resources,
                [_config.Resource(pathlib.Path("."), [pathlib.Path("./file")])],
            )

        with self.subTest("resources (src+dst)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "resources": [["dir", ["file"]]],
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(
                config.bundles[0].resources,
                [_config.Resource(pathlib.Path("dir"), [pathlib.Path("./file")])],
            )

        with self.subTest("resources (simple and src+dst)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "resources": ["source", ["dir", ["file"]]],
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(
                config.bundles[0].resources,
                [
                    _config.Resource(pathlib.Path("."), [pathlib.Path("./source")]),
                    _config.Resource(pathlib.Path("dir"), [pathlib.Path("./file")]),
                ],
            )

        with self.subTest("resources (same destination)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "test": {
                                    "script": "scriptmod.py",
                                    "resources": [
                                        "source1",
                                        "source2",
                                    ],
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(
                config.bundles[0].resources,
                [
                    _config.Resource(pathlib.Path("."), [pathlib.Path("./source1")]),
                    _config.Resource(pathlib.Path("."), [pathlib.Path("./source2")]),
                ],
            )

        with self.subTest("resources (invalid type)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "tool.py2app.bundle.test.resources' is not a list",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "main.py",
                                        "resources": "no/such/file.plist",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("resources (invalid item type)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.test.resources: invalid item 42",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "test": {
                                        "script": "main.py",
                                        "resources": [42],
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

    def test_bundle_options_inherited(self):
        # Test that options that match those in Py2appConfiguration are parsed
        # correctly.
        # XXX: These tests are a copy of the tests in test_global_options
        with self.subTest("default configuration"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                }
                            }
                        }
                    }
                },
                pathlib.Path("."),
            )

            platform = sysconfig.get_platform()
            osname, osrelease, cpuarch = platform.split("-")

            self.assertEqual(config.bundles[0].deployment_target, osrelease)
            self.assertEqual(config.bundles[0].macho_strip, True)
            self.assertEqual(config.bundles[0].macho_arch, cpuarch)
            self.assertEqual(config.bundles[0].python_optimize, sys.flags.optimize)
            self.assertEqual(config.bundles[0].python_verbose, bool(sys.flags.verbose))
            self.assertEqual(config.bundles[0].python_use_pythonpath, False)
            self.assertEqual(config.bundles[0].python_use_sitepackages, False)
            self.assertEqual(config.bundles[0].python_use_faulthandler, False)

        with self.subTest("deployment-target (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                    "deployment-target": "10.1",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].deployment_target, "10.1")

            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                    "deployment-target": "13",
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].deployment_target, "13")

        with self.subTest("deployment-target (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.main.deployment-target' is not valid",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "deployment-target": 42,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.main.deployment-target' is not valid",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "deployment-target": "catalina",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.main.deployment-target' is not valid",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "deployment-target": "10.15.3",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.main.deployment-target' is not valid",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "deployment-target": "10_15",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("strip (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                    "strip": True,
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].macho_strip, True)

            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                    "strip": False,
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].macho_strip, False)

        with self.subTest("strip (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.main.strip' is not a boolean",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "strip": "off",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("build-type (valid)"):
            for value in ("standalone", "semi-standalone", "alias"):
                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "build-type": value,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(config.bundles[0].build_type, _config.BuildType(value))

        with self.subTest("build-type (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.main.build-type' has invalid value",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "build-type": "off",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("arch (valid)"):
            for value in ("x86_64", "arm64", "universal2"):
                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "arch": value,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(config.bundles[0].macho_arch, value)

        with self.subTest("arch (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.main.arch' has invalid value",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "arch": "off",
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("python.optimize (valid)"):
            config = _config.parse_pyproject(
                {
                    "tool": {
                        "py2app": {
                            "bundle": {
                                "main": {
                                    "script": "main.py",
                                    "python": {
                                        "optimize": 42,
                                    },
                                }
                            },
                        }
                    }
                },
                pathlib.Path("."),
            )
            self.assertEqual(config.bundles[0].python_optimize, 42)

        with self.subTest("python.optimize (invalid)"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.main.python.optimize' is not an integer",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "python": {
                                            "optimize": "off",
                                        },
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        for subkey, attribute in [
            ("verbose", "python_verbose"),
            ("use-pythonpath", "python_use_pythonpath"),
            ("use-sitepackages", "python_use_sitepackages"),
            ("use-faulthandler", "python_use_faulthandler"),
        ]:
            with self.subTest("setting python.{subkey} (valid)"):
                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "python": {subkey: True},
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(getattr(config.bundles[0], attribute), True)

                config = _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "python": {subkey: False},
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )
                self.assertEqual(getattr(config.bundles[0], attribute), False)

            with self.subTest(f"setting {subkey} (invalid)"):
                with self.assertRaisesRegex(
                    _config.ConfigurationError,
                    f"'tool.py2app.bundle.main.python.{subkey}' is not a boolean",
                ):
                    _config.parse_pyproject(
                        {
                            "tool": {
                                "py2app": {
                                    "bundle": {
                                        "main": {
                                            "script": "main.py",
                                            "python": {
                                                subkey: "hello",
                                            },
                                        }
                                    },
                                }
                            }
                        },
                        pathlib.Path("."),
                    )

        with self.subTest("invalid python key"):
            with self.assertRaisesRegex(
                _config.ConfigurationError,
                "'tool.py2app.bundle.main.python' is not a dictionary",
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "python": 42,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

        with self.subTest("invalid key"):
            with self.assertRaisesRegex(
                _config.ConfigurationError, "invalid key 'tool.py2app.bundle.main.foo'"
            ):
                _config.parse_pyproject(
                    {
                        "tool": {
                            "py2app": {
                                "bundle": {
                                    "main": {
                                        "script": "main.py",
                                        "foo": 42,
                                    }
                                },
                            }
                        }
                    },
                    pathlib.Path("."),
                )

    def test_two_bundles(self):
        config = _config.parse_pyproject(
            {
                "tool": {
                    "py2app": {
                        "bundle": {
                            "main": {
                                "script": "main.py",
                            },
                            "sub": {
                                "script": "sub.py",
                            },
                        },
                    }
                }
            },
            pathlib.Path("."),
        )
        self.assertEqual(len(config.bundles), 2)
        self.assertEqual(config.bundles[0].script, pathlib.Path("./main.py"))
        self.assertEqual(config.bundles[1].script, pathlib.Path("./sub.py"))

    def test_global_options_in_bundle_options(self):
        # Check that every global option is also present on the bundle options,
        # excluding 'bundles' and 'recipe'.
        global_options = set(dir(_config.Py2appConfiguration([], 2, 3)))
        local_options = set(dir(_config.BundleOptions(1, 2)))

        self.assertEqual(global_options - local_options, {"bundles", "recipe"})
