import os
import plistlib
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
    app_dir = os.path.join(DIR_NAME, "app_with_data")

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

    def assertContentsEqual(self, src_file, dst_file):
        fp = open(src_file, "rb")
        src_data = fp.read()
        fp.close()

        fp = open(dst_file, "rb")
        dst_data = fp.read()
        fp.close()

        self.assertEqual(src_data, dst_data)

    def test_icon_file(self):
        resource_dir = os.path.join(
            self.app_dir, "dist", "SimpleApp.app", "Contents", "Resources"
        )

        with open(os.path.join(resource_dir, "..", "Info.plist"), "rb") as fp:
            if hasattr(plistlib, "load"):
                pl = plistlib.load(fp)
            else:
                pl = plistlib.readPlist(fp)

        self.assertEqual(pl["CFBundleIconFile"], "main.icns")

        src_file = os.path.join(self.app_dir, "main.icns")
        dst_file = os.path.join(resource_dir, "main.icns")
        self.assertTrue(os.path.exists(dst_file))

        self.assertContentsEqual(src_file, dst_file)

        if "--alias" in self.py2app_args:
            self.assertTrue(os.path.islink(dst_file))

    def test_resources(self):
        resource_dir = os.path.join(
            self.app_dir, "dist", "SimpleApp.app", "Contents", "Resources"
        )

        src_file = os.path.join(self.app_dir, "data3", "source.c")
        dst_file = os.path.join(resource_dir, "source.c")

        self.assertTrue(os.path.exists(dst_file))

        self.assertContentsEqual(src_file, dst_file)

        if "--alias" in self.py2app_args:
            self.assertTrue(os.path.islink(dst_file))

    def test_executable_resource(self):
        resource_dir = os.path.join(
            self.app_dir, "dist", "SimpleApp.app", "Contents", "Resources"
        )
        src_file = os.path.join(self.app_dir, "data1", "file3.sh")
        dst_file = os.path.join(resource_dir, "sub1", "file3.sh")

        src_st = os.stat(src_file)
        dst_st = os.stat(dst_file)

        self.assertEqual(
            src_st.st_mode,
            dst_st.st_mode,
            f"{src_st.st_mode:o} != {dst_st.st_mode:o}",
        )

    def test_data_files(self):
        resource_dir = os.path.join(
            self.app_dir, "dist", "SimpleApp.app", "Contents", "Resources"
        )

        for src_path, dst_path, chk_link in [
            ("data1/file1.txt", "sub1/file1.txt", True),
            ("data1/file2.txt", "sub1/file2.txt", True),
            ("data1/file3.sh", "sub1/file3.sh", True),
            ("data2/source.c", "data2/source.c", False),
        ]:
            src_file = os.path.join(self.app_dir, src_path)
            dst_file = os.path.join(resource_dir, dst_path)

            self.assertTrue(os.path.exists(dst_file))

            self.assertContentsEqual(src_file, dst_file)

            if chk_link and "--alias" in self.py2app_args:
                self.assertTrue(
                    os.path.islink(dst_file), f"{dst_file} is not a symlink"
                )

        # if '--alias' in self.py2app_args:
        #    self.assertTrue(os.path.islink(os.path.join(resource_dir, 'data2')))


class TestBasicAliasApp(TestBasicApp):
    py2app_args = [
        "--alias",
    ]


class TestBasicSemiStandaloneApp(TestBasicApp):
    py2app_args = [
        "--semi-standalone",
    ]
