import os
import shutil
import subprocess
import sys
import time
import unittest

import py2app

from .tools import kill_child_processes

DIR_NAME = os.path.dirname(os.path.abspath(__file__))


class TestBasicApp(unittest.TestCase):
    py2app_args = []
    app_dir = os.path.join(DIR_NAME, "resource_compile_app")

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
            [sys.executable, "setup.py", "py2app"] + cls.py2app_args,
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

    def assertContentsEqual(self, src_file, dst_file):
        fp = open(src_file, "rb")
        src_data = fp.read()
        fp.close()

        fp = open(dst_file, "rb")
        dst_data = fp.read()
        fp.close()

        self.assertEqual(src_data, dst_data)

    def test_resources(self):
        resource_dir = os.path.join(
            self.app_dir, "dist", "Resources.app", "Contents", "Resources"
        )

        self.assertFalse(os.path.exists(os.path.join(resource_dir, "MainMenu.xib")))
        self.assertTrue(os.path.exists(os.path.join(resource_dir, "MainMenu.nib")))

        # XXX: Need to test for other resource types as well, this
        # will do for now to test that the basic functionality works.


class TestBasicAliasApp(TestBasicApp):
    py2app_args = [
        "--alias",
    ]


class TestBasicSemiStandaloneApp(TestBasicApp):
    py2app_args = [
        "--semi-standalone",
    ]
