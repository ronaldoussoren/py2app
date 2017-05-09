"""
Testcase for checking argv_emulation
"""
import sys
if (sys.version_info[0] == 2 and sys.version_info[:2] >= (2,7)) or \
        (sys.version_info[0] == 3 and sys.version_info[:2] >= (3,2)):
    import unittest
else:
    import unittest2 as unittest

import subprocess
import shutil
import time
import os
import signal
import platform
import py2app
from distutils.version import LooseVersion
if __name__ == "__main__":
    from tools import kill_child_processes
else:
    from .tools import kill_child_processes

DIR_NAME=os.path.dirname(os.path.abspath(__file__))


class TestArgvEmulation (unittest.TestCase):
    py2app_args = []
    setup_file = "setup.py"
    open_argument = '/usr/bin/ssh'
    app_dir = os.path.join(DIR_NAME, 'argv_app')

    # Basic setup code
    #
    # The code in this block needs to be moved to
    # a base-class.
    @classmethod
    def setUpClass(cls):
        kill_child_processes()

        env=os.environ.copy()
        pp = os.path.dirname(os.path.dirname(py2app.__file__))
        env['TMPDIR'] = os.getcwd()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = pp + ':' + env['PYTHONPATH']
        else:
            env['PYTHONPATH'] = pp

        p = subprocess.Popen([
                sys.executable,
                    cls.setup_file, 'py2app'] + cls.py2app_args,
            cwd = cls.app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=False,
            env=env)
        lines = p.communicate()[0]
        if p.wait() != 0:
            print (lines)
            raise AssertionError("Creating basic_app bundle failed")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(os.path.join(cls.app_dir, 'build')):
            shutil.rmtree(os.path.join(cls.app_dir, 'build'))

        if os.path.exists(os.path.join(cls.app_dir, 'dist')):
            shutil.rmtree(os.path.join(cls.app_dir, 'dist'))

        time.sleep(2)

    def tearDown(self):
        kill_child_processes()
        time.sleep(1)


    #
    # End of setup code
    #

    def test_basic_start(self):
        self.maxDiff = None

        path = os.path.join( self.app_dir, 'dist/argv.txt')
        if os.path.exists(path):
            os.unlink(path)

        path = os.path.join( self.app_dir, 'dist/BasicApp.app')

        p = subprocess.Popen(["/usr/bin/open",
            '-a', path])
        exit = p.wait()

        self.assertEqual(exit, 0)

        path = os.path.join( self.app_dir, 'dist/argv.txt')
        for x in range(70):     # Argv emulation can take up-to 60 seconds
            time.sleep(1)
            if os.path.exists(path):
                break

        self.assertTrue(os.path.isfile(path))

        fp = open(path)
        data = fp.read().strip()
        fp.close()

        self.assertEqual(data.strip(), repr([os.path.join(self.app_dir, 'dist/BasicApp.app/Contents/Resources/main.py')]))

    def test_start_with_args(self):
        self.maxDiff = None

        path = os.path.join( self.app_dir, 'dist/argv.txt')
        if os.path.exists(path):
            os.unlink(path)

        path = os.path.join( self.app_dir, 'dist/BasicApp.app')

        p = subprocess.Popen(["/usr/bin/open",
            '-a', path, self.open_argument])
        exit = p.wait()

        self.assertEqual(exit, 0)

        path = os.path.join( self.app_dir, 'dist/argv.txt')
        for x in range(90):     # Argv emulation can take up-to 60 seconds
            time.sleep(1)
            if os.path.exists(path):
                break

        self.assertTrue(os.path.isfile(path))

        fp = open(path, 'r')
        data = fp.read().strip()
        fp.close()

        self.assertEqual(data.strip(), repr([os.path.join(self.app_dir, 'dist/BasicApp.app/Contents/Resources/main.py'), self.open_argument]))

    @unittest.skipIf(LooseVersion(platform.mac_ver()[0]) < LooseVersion('10.6'), "Test cannot work on OSX 10.5 or earlier")
    def test_start_with_two_args(self):
        if not self.open_argument.startswith('/'):
            unittest.skip("Only relevant for base class")

        path = os.path.join( self.app_dir, 'dist/argv.txt')
        if os.path.exists(path):
            os.unlink(path)

        self.maxDiff = None
        path = os.path.join( self.app_dir, 'dist/BasicApp.app')

        p = subprocess.Popen(["/usr/bin/open",
                '-a', path, "--args", "one", "two", "three"])
        exit = p.wait()
        self.assertEqual(exit, 0)

        path = os.path.join( self.app_dir, 'dist/argv.txt')
        for x in range(70):     # Argv emulation can take up-to 60 seconds
            time.sleep(1)
            if os.path.exists(path):
                time.sleep(5)
                break

        self.assertTrue(os.path.isfile(path))

        fp = open(path, 'r')
        data = fp.read().strip()
        fp.close()

        self.assertEqual(data.strip(), repr([os.path.join(self.app_dir, 'dist/BasicApp.app/Contents/Resources/main.py'), "one", "two", "three"]))

class TestArgvEmulationWithURL (TestArgvEmulation):
    py2app_args = []
    setup_file = "setup-with-urlscheme.py"
    open_argument = 'myurl:mycommand'
    app_dir = os.path.join(DIR_NAME, 'argv_app')


if __name__ == "__main__":
    unittest.main()
