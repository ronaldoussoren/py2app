"""
Simular to test_basic_app, but for plugin bundles
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
from distutils.sysconfig import get_config_var

DIR_NAME=os.path.dirname(os.path.abspath(__file__))

if sys.version_info[0] == 2:
    def B(value):
        return value

else:
    def B(value):
        return value.encode('latin1')



class TestBasicPlugin (unittest.TestCase):
    py2app_args = []

    # Basic setup code
    #
    # The code in this block needs to be moved to
    # a base-class.
    @classmethod
    def setUpClass(cls):
        cmd = [ sys.executable, 'setup.py', 'py2app'] + cls.py2app_args
        
        p = subprocess.Popen(
            cmd,
            cwd = os.path.join(DIR_NAME, 'basic_plugin'),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True)
        lines = p.communicate()[0]
        if p.wait() != 0:
            print (lines)
            raise AssertionError("Creating basic_plugin bundle failed")

        p = subprocess.Popen([
            'gcc'] +  get_config_var('LDFLAGS').split() + [ 
                '-o', 'bundle_loader', os.path.join(DIR_NAME, 'bundle_loader.m'), 
                '-framework', 'Foundation'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True)
        lines = p.communicate()[0]
        if p.wait() != 0:
            print (lines)
            raise AssertionError("Creating bundle_loader failed")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(os.path.join(DIR_NAME, 'basic_plugin/build')):
            shutil.rmtree(os.path.join(DIR_NAME, 'basic_plugin/build'))

        if os.path.exists(os.path.join(DIR_NAME, 'basic_plugin/dist')):
            shutil.rmtree(os.path.join(DIR_NAME, 'basic_plugin/dist'))

        if os.path.exists('bundle_loader'):
            os.unlink('bundle_loader')

    def start_app(self):
        # Start the test app, return a subprocess object where
        # stdin and stdout are connected to pipes.
        cmd = ['./bundle_loader',
                    os.path.join(DIR_NAME,
                                'basic_plugin/dist/BasicPlugin.bundle'),
        ]
        p = subprocess.Popen(cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                close_fds=True,
                )
                #stderr=subprocess.STDOUT)
        return p

    def wait_with_timeout(self, proc, timeout=10):
        for i in range(timeout):
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
        p.stdout.readline()

        p.stdin.write('BasicPlugin.bundle:test startup\n'.encode('latin1'))
        p.stdin.flush()

        v = p.stdout.readline()
        self.assertEqual(v.strip(), B('+ test startup'))

        p.stdin.close()
        p.stdout.close()

        exit = self.wait_with_timeout(p)
        self.assertEqual(exit, 0)

class TestBasicAliasPlugin (TestBasicPlugin):
    py2app_args = [ '--alias' ]

class TestBasicSemiStandalonePlugin (TestBasicPlugin):
    py2app_args = [ '--semi-standalone' ]

if __name__ == "__main__":
    unittest.main()

