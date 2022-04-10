"""
Tests for typechecking of input arguments
"""
import unittest
from py2app.build_app import py2app as py2app_cmd
from distutils.core import Distribution


class TestSetupArguments(unittest.TestCase):
    def create_cmd(self, **kwds):
        dist = Distribution(kwds)
        cmd = py2app_cmd(dist)
        cmd.dist_dir = "dist"
        cmd.fixup_distribution()
        cmd.finalize_options()

        return cmd

    def test_version(self):
        # Explicit version
        cmd = self.create_cmd(
            name="py2app_test",
            version="1.0",
            app=["main.py"],
        )
        pl = cmd.get_default_plist()
        self.assertEqual(pl["CFBundleVersion"], "1.0")

        # No version specified, none in script as well.
        cmd = self.create_cmd(
            name="py2app_test",
            app=["main.py"],
        )
        pl = cmd.get_default_plist()
        self.assertEqual(pl["CFBundleVersion"], "0.0.0")

        # A bit annoyinly distutils will automatically convert
        # integers to strings:
        cmd = self.create_cmd(name="py2app_test", app=["main.py"], version=1)
        pl = cmd.get_default_plist()
        self.assertEqual(pl["CFBundleVersion"], "1")
        self.assertEqual(cmd.distribution.get_version(), "1")


if __name__ == "__main__":
    unittest.main()
