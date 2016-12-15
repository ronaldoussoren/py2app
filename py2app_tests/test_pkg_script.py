"""
Test case for a project that includes a script that has the same
base-name as a package used by the script.
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
import zipfile
if __name__ == "__main__":
    from tools import kill_child_processes
else:
    from .tools import kill_child_processes

DIR_NAME=os.path.dirname(os.path.abspath(__file__))


class TestBasicApp (unittest.TestCase):
    py2app_args = []
    python_args = []
    app_dir = os.path.join(DIR_NAME, 'pkg_script_app')

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
            'dist/quot.app/Contents/MacOS/quot')

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

    def test_basic_start(self):
        p = self.start_app()

        p.stdin.close()

        exit = self.wait_with_timeout(p)
        self.assertEqual(exit, 0)

        p.stdout.close()

    def test_simple_imports(self):
        p = self.start_app()

        p.stdin.write(("print(%r in sys.path)\n"%(
            os.path.join(self.app_dir, 'dist/quot.app/Contents/Resources'),)).encode('latin1'))
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"False")


        # Basic module that is always present:
        p.stdin.write('import_module("os")\n'.encode('latin1'))
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"os")

        # Dependency of the main module:
        p.stdin.write('import_module("quot")\n'.encode('latin1'))
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"quot")

        # - verify that the right one gets loaded
        if '--alias' not in self.py2app_args:
            p.stdin.write('import quot;print(quot.__file__)\n'.encode('latin1'))
            p.stdin.flush()
            ln = p.stdout.readline()
            self.assertTrue(b"Contents/Resources/lib" in ln.strip())

        p.stdin.write('import_module("quot.queue")\n'.encode('latin1'))
        p.stdin.flush()
        ln = p.stdout.readline()
        self.assertEqual(ln.strip(), b"quot.queue")

        p.stdin.close()
        p.stdout.close()

    def test_zip_contents(self):
        if '--alias' in self.py2app_args:
            raise unittest.SkipTest("Not relevant for Alias builds")

        dirpath = os.path.join(self.app_dir, 'dist/quot.app/Contents')
        zfpath = os.path.join(dirpath, 'Resources/lib/python%d%d.zip'%(
            sys.version_info[:2]))
        if not os.path.exists(zfpath):
            zfpath = os.path.join(dirpath, 'Resources/lib/python%d.%d/site-packages.zip'%(
                sys.version_info[:2]))
        if not os.path.exists(zfpath):
            zfpath = os.path.join(dirpath, 'Resources/lib/site-packages.zip')

        if not os.path.exists(zfpath):
            self.fail("Cannot locate embedded zipfile")

        zf = zipfile.ZipFile(zfpath, 'r')
        for nm in ('quot.py', 'quot.pyc', 'quot.pyo'):
            try:
                zf.read(nm)
                self.fail("'quot' module is in the zipfile")
            except KeyError:
                pass


class TestBasicAliasApp (TestBasicApp):
    py2app_args = [ '--alias', ]

class TestBasicSemiStandaloneApp (TestBasicApp):
    py2app_args = [ '--semi-standalone', ]

if __name__ == "__main__":
    unittest.main()
