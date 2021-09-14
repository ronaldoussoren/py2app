import sys
if (sys.version_info[0] == 2 and sys.version_info[:2] >= (2,7)) or \
        (sys.version_info[0] == 3 and sys.version_info[:2] >= (3,2)):
    import unittest
else:
    import unittest2 as unittest

import platform
import subprocess
import shutil
import time
import os
import signal
import py2app
import hashlib
import sysconfig
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


class TestBasicAppWithPlugins (unittest.TestCase):
    py2app_args = []
    python_args = []
    app_dir = os.path.join(DIR_NAME, 'basic_app_with_plugin')

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
                    'setup.py', 'pluginexe'],
            cwd = cls.app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=False,
            env=env
            )
        lines = p.communicate()[0]
        if p.wait() != 0:
            print (lines)
            raise AssertionError("Creating plugin executable failed")

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

        p = subprocess.Popen([
                sys.executable ] + cls.python_args + [
                    'setup.py', 'cleanup'],
            cwd = cls.app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=False,
            )
        lines = p.communicate()[0]
        if p.wait() != 0:
            print (lines)
            raise AssertionError("Cleanup failed")

        time.sleep(2)

    def tearDown(self):
        kill_child_processes()
        time.sleep(1)

    #
    # End of setup code
    #

    def test_package_structure(self):
        root = os.path.join(self.app_dir, 'dist/BasicApp.app')

        path = os.path.join(
                root, 'Contents', 'Library', 'QuickLook', 'dummy1.qlgenerator')
        self.assertTrue(os.path.exists(path), '%r does not exist'%(path,))

        path = os.path.join(
                root, 'Contents', 'Library', 'Spotlight', 'dummy2.mdimporter')
        self.assertTrue(os.path.exists(path), '%r does not exist'%(path,))

class TestBasicAliasAppWithPlugins (TestBasicAppWithPlugins):
    py2app_args = [ '--alias', ]

class TestBasicSemiStandaloneAppWithPlugins (TestBasicAppWithPlugins):
    py2app_args = [ '--semi-standalone', ]


if __name__ == "__main__":
    unittest.main()
