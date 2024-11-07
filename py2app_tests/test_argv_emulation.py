"""
Testcase for checking argv_emulation
"""

import os
import shutil
import subprocess
import sys
import time
import unittest

import py2app

from .tools import kill_child_processes

DIR_NAME = os.path.dirname(os.path.abspath(__file__))


class TestArgvEmulation(unittest.TestCase):
    py2app_args = []
    setup_file = "setup.py"
    open_argument = "/usr/bin/ssh"
    app_dir = os.path.join(DIR_NAME, "argv_app")

    # Basic setup code
    #
    # The code in this block needs to be moved to
    # a base-class.
    @classmethod
    def setUpClass(cls):
        kill_child_processes()

        env = os.environ.copy()
        pp = os.path.dirname(os.path.dirname(py2app.__file__))
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = pp + ":" + env["PYTHONPATH"]
        else:
            env["PYTHONPATH"] = pp

        p = subprocess.Popen(
            [sys.executable, cls.setup_file, "py2app"] + cls.py2app_args,
            cwd=cls.app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=False,
            env=env,
        )
        lines = p.communicate()[0]
        if p.wait() != 0:
            print(lines)
            raise AssertionError("Creating basic_app bundle failed")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(os.path.join(cls.app_dir, "build")):
            shutil.rmtree(os.path.join(cls.app_dir, "build"))

        if os.path.exists(os.path.join(cls.app_dir, "dist")):
            shutil.rmtree(os.path.join(cls.app_dir, "dist"))

        time.sleep(2)

    def tearDown(self):
        kill_child_processes()
        time.sleep(1)

    #
    # End of setup code
    #

    def test_basic_start(self):
        self.maxDiff = None

        path = os.path.join(self.app_dir, "dist/argv.txt")
        if os.path.exists(path):
            os.unlink(path)

        path = os.path.join(self.app_dir, "dist/BasicApp.app")

        p = subprocess.Popen(["/usr/bin/open", "-a", path])
        status = p.wait()

        self.assertEqual(status, 0)

        path = os.path.join(self.app_dir, "dist/argv.txt")
        for _ in range(70):  # Argv emulation can take up-to 60 seconds
            time.sleep(1)
            if os.path.exists(path):
                break

        self.assertTrue(os.path.isfile(path))

        fp = open(path)
        data = fp.read().strip()
        fp.close()

        self.assertEqual(
            data.strip(),
            repr(
                [
                    os.path.join(
                        self.app_dir, "dist/BasicApp.app/Contents/Resources/main.py"
                    )
                ]
            ),
        )

    def test_start_with_args(self):
        self.maxDiff = None

        path = os.path.join(self.app_dir, "dist/argv.txt")
        if os.path.exists(path):
            os.unlink(path)

        path = os.path.join(self.app_dir, "dist/BasicApp.app")

        p = subprocess.Popen(["/usr/bin/open", "-a", path, self.open_argument])
        status = p.wait()

        self.assertEqual(status, 0)

        path = os.path.join(self.app_dir, "dist/argv.txt")
        for _ in range(90):  # Argv emulation can take up-to 60 seconds
            time.sleep(1)
            if os.path.exists(path):
                break

        self.assertTrue(os.path.isfile(path))

        fp = open(path)
        data = fp.read().strip()
        fp.close()

        self.assertEqual(
            data.strip(),
            repr(
                [
                    os.path.join(
                        self.app_dir, "dist/BasicApp.app/Contents/Resources/main.py"
                    ),
                    self.open_argument,
                ]
            ),
        )

    def test_start_with_two_args(self):
        if not self.open_argument.startswith("/"):
            unittest.skip("Only relevant for base class")

        path = os.path.join(self.app_dir, "dist/argv.txt")
        if os.path.exists(path):
            os.unlink(path)

        self.maxDiff = None
        path = os.path.join(self.app_dir, "dist/BasicApp.app")

        p = subprocess.Popen(
            ["/usr/bin/open", "-a", path, "--args", "one", "two", "three"]
        )
        status = p.wait()
        self.assertEqual(status, 0)

        path = os.path.join(self.app_dir, "dist/argv.txt")
        for _ in range(70):  # Argv emulation can take up-to 60 seconds
            time.sleep(1)
            if os.path.exists(path):
                time.sleep(5)
                break

        self.assertTrue(os.path.isfile(path))

        fp = open(path)
        data = fp.read().strip()
        fp.close()

        self.assertEqual(
            data.strip(),
            repr(
                [
                    os.path.join(
                        self.app_dir, "dist/BasicApp.app/Contents/Resources/main.py"
                    ),
                    "one",
                    "two",
                    "three",
                ]
            ),
        )


class TestArgvEmulationWithURL(TestArgvEmulation):
    py2app_args = []
    setup_file = "setup-with-urlscheme.py"
    open_argument = "myurl:mycommand"
    app_dir = os.path.join(DIR_NAME, "argv_app")
