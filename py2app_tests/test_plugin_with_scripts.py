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
from distutils.version import LooseVersion
import py2app
import platform
if __name__ == "__main__":
    from tools import kill_child_processes
else:
    from .tools import kill_child_processes

DIR_NAME=os.path.dirname(os.path.abspath(__file__))


class TestBasicPlugin (unittest.TestCase):
    plugin_dir = os.path.join(DIR_NAME, 'plugin_with_scripts')
    py2app_args = []

    # Basic setup code
    #
    # The code in this block needs to be moved to
    # a base-class.
    @classmethod
    def setUpClass(cls):
        try:
            if os.path.exists(os.path.join(cls.plugin_dir, 'build')):
                shutil.rmtree(os.path.join(cls.plugin_dir, 'build'))

            if os.path.exists(os.path.join(cls.plugin_dir, 'dist')):
                shutil.rmtree(os.path.join(cls.plugin_dir, 'dist'))

            cmd = [ sys.executable, 'setup.py', 'py2app'] + cls.py2app_args

            env=os.environ.copy()
            env['TMPDIR'] = os.getcwd()
            pp = os.path.dirname(os.path.dirname(py2app.__file__))
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = pp + ':' + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = pp

            if 'LANG' not in env:
                env['LANG'] = 'en_US.UTF-8'


            p = subprocess.Popen(
                cmd,
                cwd = cls.plugin_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                close_fds=False,
                env=env)
            lines = p.communicate()[0]
            if p.wait() != 0:
                print (lines)
                raise AssertionError("Creating basic_plugin bundle failed")

            p = subprocess.Popen([
                'xcode-select', '-print-path'
            ], stdout = subprocess.PIPE)
            lines = p.communicate()[0]
            xit = p.wait()
            if p.wait() != 0:
                raise AssertionError("Fetching Xcode root failed")

            root = lines.strip()
            if sys.version_info[0] != 2:
                root = root.decode('utf-8')

            if LooseVersion(platform.mac_ver()[0]) < LooseVersion('10.7'):
                cc = [get_config_var('CC')]
                env = dict(os.environ)
                env['MACOSX_DEPLOYMENT_TARGET'] = get_config_var('MACOSX_DEPLOYMENT_TARGET')
            else:
                cc = ['xcrun', 'clang']
                env = dict(os.environ)

            p = subprocess.Popen(cc
                +  get_config_var('LDFLAGS').split() + get_config_var('CFLAGS').split() + [
                    '-o', 'bundle_loader', os.path.join(DIR_NAME, 'bundle_loader.m'),
                    '-framework', 'Foundation'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                close_fds=False)
            lines = p.communicate()[0]
            if p.wait() != 0:
                print (lines)
                raise AssertionError("Creating bundle_loader failed")


        except:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        if os.path.exists('bundle_loader'):
            os.unlink('bundle_loader')

        if os.path.exists(os.path.join(cls.plugin_dir, 'build')):
            shutil.rmtree(os.path.join(cls.plugin_dir, 'build'))

        if os.path.exists(os.path.join(cls.plugin_dir, 'dist')):
            shutil.rmtree(os.path.join(cls.plugin_dir, 'dist'))

        time.sleep(2)

    def tearDown(self):
        kill_child_processes()
        time.sleep(1)

    def start_app(self):
        # Start the test app, return a subprocess object where
        # stdin and stdout are connected to pipes.
        cmd = ['./bundle_loader',
                    os.path.join(self.plugin_dir,
                                'dist/BasicPlugin.bundle'),
        ]
        p = subprocess.Popen(cmd,
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

    def run_script(self, name):
        path = os.path.join(
                self.plugin_dir,
            'dist/BasicPlugin.bundle/Contents/MacOS/%s'%(name,))

        p = subprocess.Popen([path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                close_fds=False,
                )
                #stderr=subprocess.STDOUT)
        return p
    #
    # End of setup code
    #


    def test_helper1(self):
        p = self.run_script('helper1')
        lines = p.communicate()[0]
        p.wait()

        self.assertEqual(lines, b'Helper 1\n')

    def test_helper2(self):
        p = self.run_script('helper2')
        lines = p.communicate()[0]
        p.wait()

        self.assertEqual(lines, b'Helper 2\n')

    def test_basic_start(self):
        p = self.start_app()
        v = p.stdout.readline()

        self.assertFalse(v.startswith(b'** Cannot load bundle'))

        p.stdin.write('BasicPlugin.bundle:test startup\n'.encode('latin1'))
        p.stdin.flush()

        v = p.stdout.readline()
        self.assertEqual(v.strip(), b'+ test startup')

        p.stdin.close()
        p.stdout.close()

        exit = self.wait_with_timeout(p)
        self.assertEqual(exit, 0)

class TestBasicAliasPlugin (TestBasicPlugin):
    py2app_args = [ '--alias' ]

class TestBasicSemiStandalonePlugin (TestBasicPlugin):
    py2app_args = [ '--semi-standalone' ]


class TestBasicPluginUnicodePath (TestBasicPlugin):
    if sys.version_info[0] == 2:
        plugin_dir = os.path.join(DIR_NAME, 'basic_plugin ' + unichr(2744).encode('utf-8'))
    else:
        plugin_dir = os.path.join(DIR_NAME, 'basic_plugin ' + chr(2744))

    @classmethod
    def setUpClass(cls):
        kill_child_processes()

        try:
            if os.path.exists(cls.plugin_dir):
                shutil.rmtree(cls.plugin_dir)

            assert not os.path.exists(cls.plugin_dir)
            shutil.copytree(TestBasicPlugin.plugin_dir, cls.plugin_dir)

            super(TestBasicPluginUnicodePath, cls).setUpClass()

        except:
            if os.path.exists(cls.plugin_dir):
                shutil.rmtree(cls.plugin_dir)
            raise

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.plugin_dir):
            shutil.rmtree(cls.plugin_dir)

        super(TestBasicPluginUnicodePath, cls).tearDownClass()


class TestBasicAliasPluginUnicodePath (TestBasicPluginUnicodePath):
    py2app_args = [ '--alias' ]

class TestBasicSemiStandalonePluginUnicodePath (TestBasicPluginUnicodePath):
    py2app_args = [ '--semi-standalone' ]

if __name__ == "__main__":
    unittest.main()
