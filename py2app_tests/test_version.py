import os
import unittest

class TestVersions (unittest.TestCase):
    def test_package_version(self):
        import py2app

        fn = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'setup.py')
        with open(fn, 'r') as fp:
            for ln in fp:
                ln = ln.strip()
                if ln.startswith("version"):
                    version = ln.split('=')[-1].strip()
                    version = version.split(',')[0].strip()
                    break

            else:
                self.fail("Cannot find setup version")

            version = version.strip('"')

        self.assertEqual(version, py2app.__version__)

if __name__ == "__main__":
    unittest.main()

