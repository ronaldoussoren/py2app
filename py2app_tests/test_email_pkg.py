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


class TestEmailCompat(unittest.TestCase):
    py2app_args = []
    python_args = []
    setup_file = "setup-compat.py"
    app_dir = os.path.join(DIR_NAME, "app_with_email")

    # Basic setup code
    #
    # The code in this block needs to be moved to
    # a base-class.
    @classmethod
    def setUpClass(cls):
        kill_child_processes()

        env = os.environ.copy()
        env["TMPDIR"] = os.getcwd()
        pp = os.path.dirname(os.path.dirname(py2app.__file__))
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = pp + ":" + env["PYTHONPATH"]
        else:
            env["PYTHONPATH"] = pp

        if "LANG" not in env:
            # Ensure that testing though SSH works
            env["LANG"] = "en_US.UTF-8"

        p = subprocess.Popen(
            [sys.executable]
            + cls.python_args
            + [cls.setup_file, "py2app"]
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
            raise AssertionError("Creating basic_app bundle failed")

        cls.checksums = make_checksums(os.path.join(cls.app_dir, "dist/BasicApp.app"))

    def assertChecksumsSame(self):
        self.assertEqual(
            self.checksums,
            make_checksums(os.path.join(self.app_dir, "dist/BasicApp.app")),
        )

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

    def start_app(self):
        # Start the test app, return a subprocess object where
        # stdin and stdout are connected to pipes.
        path = os.path.join(self.app_dir, "dist/BasicApp.app/Contents/MacOS/BasicApp")

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


class TestEmailFull(TestEmailCompat):
    setup_file = "setup-all.py"


class TestEmailPlainImport(TestEmailCompat):
    setup_file = "setup-plain.py"
