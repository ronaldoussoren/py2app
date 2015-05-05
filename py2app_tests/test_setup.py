"""
Tests for typechecking of input arguments
"""
import sys
if (sys.version_info[0] == 2 and sys.version_info[:2] >= (2,7)) or \
    (sys.version_info[0] == 3 and sys.version_info[:2] >= (3,2)):
    import unittest
else:
    import unittest2 as unittest

from py2app.build_app import py2app as py2app_cmd
from distutils.core import Distribution
from distutils.errors import *

class TestSetupArguments (unittest.TestCase):
    def create_cmd(self, **kwds):
        dist = Distribution(kwds)
        cmd = py2app_cmd(dist)
        cmd.dist_dir = 'dist'
        cmd.fixup_distribution()
        cmd.finalize_options()

        return cmd

    def test_version(self):
        # Explicit version
        cmd = self.create_cmd(
            name='py2app_test',
            version='1.0',
            app=['main.py'],
        )
        pl = cmd.get_default_plist()
        self.assertEqual(pl['CFBundleVersion'], '1.0')

        # No version specified, none in script as well.
        cmd = self.create_cmd(
            name='py2app_test',
            app=['main.py'],
        )
        pl = cmd.get_default_plist()
        self.assertEqual(pl['CFBundleVersion'], '0.0.0')

        # A bit annoyinly distutils will automaticly convert
        # integers to strings:
        cmd = self.create_cmd(
            name='py2app_test',
            app=['main.py'],
            version=1
        )
        pl = cmd.get_default_plist()
        self.assertEqual(pl['CFBundleVersion'], '1')
        self.assertEqual(cmd.distribution.get_version(), '1')


        # Invalid types for version
        for ver in [ (1, 0), [1, 1]]:
            try:
                cmd = self.create_cmd(
                    name='py2app_test',
                    version=ver,
                    app=['main.py'],
                )
            except TypeError:
                # Workaround for bug in setuptools,
                # see <https://bitbucket.org/pypa/setuptools/issue/379>
                continue


            else:
                self.assertRaises(DistutilsOptionError, cmd.get_default_plist)

        if sys.version_info[0] > 2:
            # Avoid bytes version as well for Python 3.x
            cmd = self.create_cmd(
                name='py2app_test',
                version='1.0'.encode('ascii'),
                app=['main.py'],
            )
            self.assertRaises(DistutilsOptionError, cmd.get_default_plist)


if __name__ == "__main__":
    unittest.main()
