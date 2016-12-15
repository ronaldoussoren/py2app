"""
Testcase for checking emulate_shell_environment
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
import py2app
if __name__ == "__main__":
    from tools import kill_child_processes
else:
    from .tools import kill_child_processes

DIR_NAME=os.path.dirname(os.path.abspath(__file__))

class TestShellEnvironment (unittest.TestCase):
    py2app_args = []
    setup_file = "setup.py"
    app_dir = os.path.join(DIR_NAME, 'shell_app')

    # Basic setup code
    #
    # The code in this block needs to be moved to
    # a base-class.
    @classmethod
    def setUpClass(cls):
        kill_child_processes()

        env=os.environ.copy()
        env['TMPDIR'] = os.getcwd()
        pp = os.path.dirname(os.path.dirname(py2app.__file__))
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

    def test_shell_environment(self):
        self.maxDiff = None
        path = os.path.join( self.app_dir, 'dist/BasicApp.app')

        p = subprocess.Popen(["/usr/bin/open",
            '-a', path])
        exit = p.wait()

        self.assertEqual(exit, 0)

        path = os.path.join( self.app_dir, 'dist/env.txt')
        for x in range(25):
            time.sleep(1)
            if os.path.exists(path):
                break

        self.assertTrue(os.path.isfile(path))

        fp = open(path)
        data = fp.read().strip()
        fp.close()

        env = eval(data)
        path = env['PATH']

        self.assertNotEqual(path, '/usr/bin:/bin')

        elems = path.split(':')
        self.assertIn('/usr/bin', elems)



if __name__ == "__main__":
    unittest.main()
