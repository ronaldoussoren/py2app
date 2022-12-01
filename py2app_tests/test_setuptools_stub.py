from unittest import TestCase, mock


class TestSetuptoolsConfiguration(TestCase):
    @mock.patch("py2app._setuptools_stub.py2app.run")
    def test_default_config(self, run_mock):
        ...
