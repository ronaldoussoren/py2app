# Temporary tests to detect common issues caused
# by switching between the 2.0 and 0.28 branches
# during development.
import pathlib
from unittest import TestCase


class TestEnvironmentHealth(TestCase):
    def test_health(self):
        if pathlib.Path("py2app.egg-info").exists():
            self.fail("Old 'py2app.egg-info' found")

        if pathlib.Path("py2app").exists():
            self.fail("Old 'py2app' source tree found")
