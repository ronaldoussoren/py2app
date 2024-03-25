"""
Simular to test_basic_app, but for plugin bundles
"""

import os
import shutil
import signal
import subprocess
import sys
import time
import unittest
from distutils.sysconfig import get_config_var

import py2app

from .tools import kill_child_processes

DIR_NAME = os.path.dirname(os.path.abspath(__file__))


class TestBasicPlugin(unittest.TestCase):
    plugin_dir = os.path.join(DIR_NAME, "basic_plugin")
    py2app_args = []

    # Basic setup code
    #
    # The code in this block needs to be moved to
    # a base-class.
    @classmethod
    def setUpClass(cls):
        kill_child_processes()

        try:
            if os.path.exists(os.path.join(cls.plugin_dir, "build")):
                shutil.rmtree(os.path.join(cls.plugin_dir, "build"))

            if os.path.exists(os.path.join(cls.plugin_dir, "dist")):
                shutil.rmtree(os.path.join(cls.plugin_dir, "dist"))

            cmd = [sys.executable, "setup.py", "py2app"] + cls.py2app_args

            env = os.environ.copy()
            pp = os.path.dirname(os.path.dirname(py2app.__file__))
            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = pp + ":" + env["PYTHONPATH"]
            else:
                env["PYTHONPATH"] = pp

            if "LANG" not in env:
                env["LANG"] = "en_US.UTF-8"

            p = subprocess.Popen(
                cmd,
                cwd=cls.plugin_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                close_fds=False,
                env=env,
            )
            lines = p.communicate()[0]
            if p.wait() != 0:
                print(lines)
                try:
                    os.waitpid(0, 0)
                except OSError:
                    pass
                raise AssertionError("Creating basic_plugin bundle failed")

            p = subprocess.Popen(
                ["xcode-select", "-print-path"], stdout=subprocess.PIPE
            )
            lines = p.communicate()[0]
            if p.wait() != 0:
                try:
                    os.waitpid(0, 0)
                except OSError:
                    pass
                raise AssertionError("Fetching Xcode root failed")

            cc = ["xcrun", "clang"]
            env = dict(os.environ)

            cflags = get_config_var("CFLAGS").split()
            ldflags = get_config_var("LDFLAGS").split()

            p = subprocess.Popen(
                cc
                + ldflags
                + cflags
                + [
                    "-o",
                    "bundle_loader",
                    os.path.join(DIR_NAME, "bundle_loader.m"),
                    "-framework",
                    "Foundation",
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                close_fds=False,
            )
            lines = p.communicate()[0]
            if p.wait() != 0:
                print(lines)
                try:
                    os.waitpid(0, 0)
                except OSError:
                    pass
                raise AssertionError("Creating bundle_loader failed")

            try:
                os.waitpid(0, 0)
            except OSError:
                pass

        except:  # noqa: E722, B001
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        if os.path.exists("bundle_loader"):
            os.unlink("bundle_loader")

        if os.path.exists(os.path.join(cls.plugin_dir, "build")):
            shutil.rmtree(os.path.join(cls.plugin_dir, "build"))

        if os.path.exists(os.path.join(cls.plugin_dir, "dist")):
            shutil.rmtree(os.path.join(cls.plugin_dir, "dist"))

        if os.path.exists("bundle_loader.dSYM"):
            shutil.rmtree("bundle_loader.dSYM")

        time.sleep(2)

    def start_app(self):
        # Start the test app, return a subprocess object where
        # stdin and stdout are connected to pipes.
        cmd = [
            "./bundle_loader",
            os.path.join(self.plugin_dir, "dist/BasicPlugin.bundle"),
        ]
        p = self._p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            close_fds=False,
        )
        # stderr=subprocess.STDOUT)
        return p

    def tearDown(self):
        kill_child_processes()
        time.sleep(1)

    def wait_with_timeout(self, proc, timeout=10):
        for _ in range(timeout):
            x = proc.poll()
            if x is None:
                time.sleep(1)
            else:
                return x

        os.kill(proc.pid, signal.SIGKILL)
        return proc.wait()

    #
    # End of setup code
    #

    def test_basic_start(self):
        p = self.start_app()
        v = p.stdout.readline()

        self.assertFalse(v.startswith(b"** Cannot load bundle"))

        p.stdin.write(b"BasicPlugin.bundle:test startup\n")
        p.stdin.flush()

        v = p.stdout.readline()
        self.assertEqual(v.strip(), b"+ test startup")

        p.stdin.close()
        p.stdout.close()

        status = self.wait_with_timeout(p)
        self.assertEqual(status, 0)

    def test_python_executable_mode(self):
        path = os.path.join(
            self.plugin_dir, "dist/BasicPlugin.bundle/Contents/MacOS/python"
        )

        self.assertTrue(os.path.exists(path))
        mode = os.stat(path).st_mode
        self.assertTrue(mode & 0o001, "Not executable for other")
        self.assertTrue(mode & 0o010, "Not executable for group")
        self.assertTrue(mode & 0o100, "Not executable for user")


class TestBasicAliasPlugin(TestBasicPlugin):
    py2app_args = ["--alias"]


class TestBasicSemiStandalonePlugin(TestBasicPlugin):
    py2app_args = ["--semi-standalone"]


class TestBasicPluginUnicodePath(TestBasicPlugin):
    plugin_dir = os.path.join(DIR_NAME, "basic_plugin " + chr(2744))

    @classmethod
    def setUpClass(cls):
        try:
            if os.path.exists(cls.plugin_dir):
                shutil.rmtree(cls.plugin_dir)

            assert not os.path.exists(cls.plugin_dir)
            shutil.copytree(TestBasicPlugin.plugin_dir, cls.plugin_dir)

            super().setUpClass()

        except:  # noqa: E722, B001
            if os.path.exists(cls.plugin_dir):
                shutil.rmtree(cls.plugin_dir)
            raise

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.plugin_dir):
            shutil.rmtree(cls.plugin_dir)

        super().tearDownClass()


class TestBasicAliasPluginUnicodePath(TestBasicPluginUnicodePath):
    py2app_args = ["--alias"]


class TestBasicSemiStandalonePluginUnicodePath(TestBasicPluginUnicodePath):
    py2app_args = ["--semi-standalone"]
