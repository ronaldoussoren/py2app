"""
Testcase that tests a python package that contains data files

See also issue #53 on the py2app tracker
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
import hashlib
from modulegraph import zipio
if __name__ == "__main__":
    from tools import kill_child_processes
else:
    from .tools import kill_child_processes

DIR_NAME=os.path.dirname(os.path.abspath(__file__))


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
                with open(p, 'rb') as fp:
                    block = fp.read(10240)
                    while block:
                        h.update(block)
                        block = fp.read(10240)

                result[p] = h.hexdigest()

class TestExplicitIncludes (unittest.TestCase):
    py2app_args = [ '--includes=package2.sub' ]
    python_args = []
    app_dir = os.path.join(DIR_NAME, 'basic_app')

    maxDiff = None

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

        if 'LANG' not in env:
            # Ensure that testing though SSH works
            env['LANG'] = 'en_US.UTF-8'

        p = subprocess.Popen([
                sys.executable ] + cls.python_args + [
                    'setup.py', 'py2app'] + cls.py2app_args,
            cwd = cls.app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=False,
            env=env
            )
        lines = p.communicate()[0]
        if p.wait() != 0:
            print (lines)
            raise AssertionError("Creating basic_app bundle failed")

        cls.checksums = make_checksums(
                os.path.join(cls.app_dir, 'dist/BasicApp.app'))

    def assertChecksumsSame(self):
        self.assertEqual(self.checksums,
            make_checksums(
                os.path.join(self.app_dir, 'dist/BasicApp.app')))

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

    def start_app(self):
        # Start the test app, return a subprocess object where
        # stdin and stdout are connected to pipes.
        path = os.path.join(
                self.app_dir,
            'dist/BasicApp.app/Contents/MacOS/BasicApp')

        p = subprocess.Popen([path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                close_fds=False,
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

    def test_package_data(self):
        p = self.start_app()
        p.stdin.write('import_module("package2.sub")\n'.encode('latin1'))
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"package2.sub")

        p.stdin.write('import package2.sub\n'.encode('latin1'))
        p.stdin.write('print(package2.sub.__file__)\n'.encode('latin1'))
        p.stdin.flush()
        ln = p.stdout.readline()
        path = ln.decode('utf-8')[:-1]


        self.assertTrue(os.path.basename(path) in ['__init__.py', '__init__.pyc', '__init__.pyo'])
        self.assertTrue(zipio.isfile(path))

        path = os.path.join(os.path.dirname(path), 'data.dat')
        self.assertTrue(zipio.isfile(path) or os.path.isfile(path))

        self.assertChecksumsSame()


    def test_simple_imports(self):
        p = self.start_app()

        # Basic module that is always present:
        p.stdin.write('import_module("package2.sub")\n'.encode('latin1'))
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"package2.sub")

        self.assertChecksumsSame()

class TestExplicitIncludesWithPackage (TestExplicitIncludes):
    py2app_args = [ '--packages=package2' ]

class TestExplicitIncludesWithPackageSemiStandalone (TestExplicitIncludes):
    py2app_args = [ '--packages=package2', '--semi-standalone' ]

class TestExplicitIncludesWithSubPackage (TestExplicitIncludes):
    py2app_args = [ '--packages=package2.sub', ]

class TestExplicitIncludesWithSubPackageSemiStandalone (TestExplicitIncludes):
    py2app_args = [ '--packages=package2.sub', '--semi-standalone' ]

if __name__ == "__main__":
    unittest.main()
