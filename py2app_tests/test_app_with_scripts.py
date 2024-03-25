"""
Test case for building an app bundle with a command-line tool, that bundle
is than queried in the various test methods to check if the app bundle
is correct.

This is basically a black-box functional test of the core py2app functionality

The app itself:
    - main script has 'if 0: import modules'
    - main script has a loop that reads and exec-s statements
    - the 'modules' module depends on a set of modules/packages through
      various forms of imports (absolute, relative, old-style python2,
      namespace packages 'pip-style', namespace package other,
      zipped eggs and non-zipped eggs, develop eggs)
    - add another test that does something simular, using virtualenv to
      manage a python installation
"""

import glob
import hashlib
import os
import shutil
import signal
import subprocess
import sys
import time
import unittest

import py2app

from .tools import kill_child_processes

DIR_NAME = os.path.dirname(os.path.abspath(__file__))


def make_checksums(path):
    result = {}
    for root, dnames, fnames in os.walk(path):
        for dn in dnames:
            result[os.path.join(root, dn)] = None

        for fn in fnames:
            h = hashlib.sha1()
            p = os.path.join(root, fn)
            if os.path.islink(p):
                result[p] = os.readlink(p)

            else:
                with open(p, "rb") as fp:
                    block = fp.read(10240)
                    while block:
                        h.update(block)
                        block = fp.read(10240)

                result[p] = h.hexdigest()


class TestBasicApp(unittest.TestCase):
    py2app_args = []
    python_args = []
    app_dir = os.path.join(DIR_NAME, "app_with_scripts")

    # Basic setup code
    #
    # The code in this block needs to be moved to
    # a base-class.
    @classmethod
    def setUpClass(cls):
        # Ensure build is clean:
        cls.class_cleanup()

        env = os.environ.copy()
        pp = os.path.dirname(os.path.dirname(py2app.__file__))
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = pp + ":" + env["PYTHONPATH"]
        else:
            env["PYTHONPATH"] = pp

        if "LANG" not in env:
            # Ensure that testing though SSH works
            env["LANG"] = "en_US.UTF-8"

        p = subprocess.Popen(
            [sys.executable] + cls.python_args + ["presetup.py", "build_ext"],
            cwd=cls.app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=False,
            env=env,
        )
        lines = p.communicate()[0]
        if p.wait() != 0:
            sys.stdout.write(lines.decode("utf-8"))
            print("Creating basic_app extension failed")
            try:
                os.waitpid(0, 0)
            except OSError:
                pass
            raise AssertionError("Creating basic_app extension failed")

        p = subprocess.Popen(
            [sys.executable]
            + cls.python_args
            + ["setup.py", "py2app"]
            + cls.py2app_args,
            cwd=cls.app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=False,
            env=env,
        )
        lines = p.communicate()[0]
        if p.wait() != 0:
            print(lines)
            print("Creating basic_app bundle failed")
            try:
                os.waitpid(0, 0)
            except OSError:
                pass
            raise AssertionError("Creating basic_app bundle failed")

        try:
            os.waitpid(0, 0)
        except OSError:
            pass

        cls.checksums = make_checksums(os.path.join(cls.app_dir, "dist/BasicApp.app"))

    def assertChecksumsSame(self):
        self.assertEqual(
            self.checksums,
            make_checksums(os.path.join(self.app_dir, "dist/BasicApp.app")),
        )

    @classmethod
    def tearDownClass(cls):
        cls.class_cleanup()

    @classmethod
    def class_cleanup(cls):
        if os.path.exists(os.path.join(cls.app_dir, "build")):
            shutil.rmtree(os.path.join(cls.app_dir, "build"))

        if os.path.exists(os.path.join(cls.app_dir, "dist")):
            shutil.rmtree(os.path.join(cls.app_dir, "dist"))

        for fn in glob.glob(os.path.join(cls.app_dir, "foo.*.so")):
            os.unlink(fn)

        if os.path.exists(os.path.join(cls.app_dir, "foo.so")):
            os.unlink(os.path.join(cls.app_dir, "foo.so"))

        time.sleep(2)

    def start_app(self):
        # Start the test app, return a subprocess object where
        # stdin and stdout are connected to pipes.
        path = os.path.join(self.app_dir, "dist/BasicApp.app/Contents/MacOS/BasicApp")

        p = self._p = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            close_fds=False,
        )
        # stderr=subprocess.STDOUT)
        return p

    def tearDown(self):
        if hasattr(self, "_p"):
            self._p.send_signal(9)
            try:
                self._p.communicate()
            except ValueError:
                pass
            self._p.wait()
        kill_child_processes()
        time.sleep(1)

    def run_script(self, name):
        path = os.path.join(self.app_dir, f"dist/BasicApp.app/Contents/MacOS/{name}")

        p = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            close_fds=False,
        )
        # stderr=subprocess.STDOUT)
        return p

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

    def test_helper1(self):
        p = self.run_script("helper1")
        lines = p.communicate()[0]
        p.wait()

        self.assertEqual(lines, b"Helper 1: curses\n")

    def test_helper2(self):
        p = self.run_script("helper2")
        lines = p.communicate()[0]
        p.wait()

        self.assertEqual(lines, b"Helper 2: 4\n")

    def test_basic_start(self):
        p = self.start_app()

        p.stdin.close()

        status = self.wait_with_timeout(p)
        self.assertEqual(status, 0)

        p.stdout.close()

        self.assertChecksumsSame()

    def test_simple_imports(self):
        p = self.start_app()

        # Basic module that is always present:
        p.stdin.write(b'import_module("os")\n')
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"os")

        # Dependency of the main module:
        p.stdin.write(b'import_module("decimal")\n')
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"decimal")

        # Dependency of 'helper1':
        p.stdin.write(b'import_module("curses")\n')
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"curses")

        p.stdin.write(b'import_module("_curses")\n')
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"_curses")

        can_import_stdlib = False
        if "--alias" in self.py2app_args:
            can_import_stdlib = True

        if "--semi-standalone" in self.py2app_args:
            can_import_stdlib = True

        if sys.prefix.startswith("/System/"):
            can_import_stdlib = True

        if not can_import_stdlib:
            # Not a dependency of the module (stdlib):
            p.stdin.write(b'import_module("turtledemo")\n')
            p.stdin.flush()
            ln = p.stdout.readline().decode("utf-8")
            self.assertTrue(ln.strip().startswith("* import failed"), ln)

        else:
            p.stdin.write(b'import_module("turtledemo")\n')
            p.stdin.flush()
            ln = p.stdout.readline()
            self.assertEqual(ln.strip(), b"turtledemo")

        if sys.prefix.startswith("/System") or "--alias" in self.py2app_args:
            # py2app is included as part of the system install
            p.stdin.write(b'import_module("py2app")\n')
            p.stdin.flush()
            ln = p.stdout.readline()
            self.assertEqual(ln.strip(), b"py2app")

        else:
            # Not a dependency of the module (external):
            p.stdin.write(b'import_module("py2app")\n')
            p.stdin.flush()
            ln = p.stdout.readline().decode("utf-8")
            self.assertTrue(ln.strip().startswith("* import failed"), ln)

        p.stdin.close()
        p.stdout.close()
        self.assertChecksumsSame()

    def test_is_optimized(self):
        p = self.start_app()

        try:
            p.stdin.write(b"print(__debug__)\n")
            p.stdin.flush()
            ln = p.stdout.readline()
            self.assertEqual(ln.strip(), b"True")

        finally:
            p.stdin.close()
            p.stdout.close()
        self.assertChecksumsSame()


class TestBasicAliasApp(TestBasicApp):
    py2app_args = [
        "--alias",
    ]


class TestBasicSemiStandaloneApp(TestBasicApp):
    py2app_args = [
        "--semi-standalone",
    ]


class TestBasicAppUnicodePath(TestBasicApp):
    app_dir = os.path.join(DIR_NAME, "basic_app " + chr(2744))

    @classmethod
    def setUpClass(cls):
        kill_child_processes()

        try:
            if os.path.exists(cls.app_dir):
                shutil.rmtree(cls.app_dir)

            assert not os.path.exists(cls.app_dir)
            shutil.copytree(TestBasicApp.app_dir, cls.app_dir)

            super().setUpClass()

        except:  # noqa: E722, B001
            if os.path.exists(cls.app_dir):
                shutil.rmtree(cls.app_dir)

            raise

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.app_dir):
            shutil.rmtree(cls.app_dir)


class TestBasicAliasAppUnicodePath(TestBasicAppUnicodePath):
    py2app_args = [
        "--alias",
    ]


class TestBasicSemiStandaloneAppUnicodePath(TestBasicAppUnicodePath):
    py2app_args = [
        "--semi-standalone",
    ]


class TestOptimized1(TestBasicApp):
    py2app_args = ["-O1"]

    def test_is_optimized(self):
        p = self.start_app()

        try:
            p.stdin.write(b"print(__debug__)\n")
            p.stdin.flush()
            ln = p.stdout.readline()
            self.assertEqual(ln.strip(), b"False")

        finally:
            p.stdin.close()
            p.stdout.close()
            p.wait()

        self.assertChecksumsSame()


class TestOptimized2(TestBasicApp):
    py2app_args = ["-O2"]

    def test_is_optimized(self):
        p = self.start_app()

        try:
            p.stdin.write(b"print(__debug__)\n")
            p.stdin.flush()
            ln = p.stdout.readline()
            self.assertEqual(ln.strip(), b"False")

        finally:
            p.stdin.close()
            p.stdout.close()
            p.wait()

        self.assertChecksumsSame()
