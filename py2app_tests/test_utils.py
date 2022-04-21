import tempfile
import textwrap
import unittest

from py2app import util


class TestVersionExtraction(unittest.TestCase):
    def assert_version_equals(self, source, version):
        with tempfile.NamedTemporaryFile("w") as stream:
            stream.write(source)
            stream.flush()

            found = util.find_version(stream.name)
            self.assertEqual(found, version)

    def test_no_version(self):
        self.assert_version_equals("x = 1", None)

    def test_simple_version(self):
        self.assert_version_equals("__version__ = 'a'", "a")

    def test_multi_part(self):
        self.assert_version_equals("__version__ = 'a' 'b'", "ab")

    def test_multi_target(self):
        self.assert_version_equals("b = __version__ = 'c'", "c")

    def test_multi_target2(self):
        self.assert_version_equals("b[x] = __version__ = 'c'", "c")

    def test_not_string(self):
        self.assert_version_equals("__version__ = 42", None)

    def test_expression(self):
        self.assert_version_equals("b = __version__ = 'c'.upper()", None)

    def test_syntax_error(self):
        with self.assertRaises(SyntaxError):
            self.assert_version_equals("__version__ = 42k", None)

    def test_multiple_assigments(self):
        self.assert_version_equals(
            textwrap.dedent(
                """\
           __version__ = 'a'
           def foo(self):
               a = 42
           __version__ = 'z'
           """
            ),
            "z",
        )

    def test_last_invalid(self):
        self.assert_version_equals(
            textwrap.dedent(
                """\
           __version__ = 'a'
           def foo(self):
               a = 42
           __version__ = 42
           """
            ),
            None,
        )

    def test_in_ifstatement(self):
        self.assert_version_equals(
            textwrap.dedent(
                """\
           if a == 42:
               __version__ = 'a'
           """
            ),
            None,
        )

    def test_in_forstatement(self):
        self.assert_version_equals(
            textwrap.dedent(
                """\
           for a in 42:
               __version__ = 'a'
           """
            ),
            None,
        )

    def test_in_whilestatement(self):
        self.assert_version_equals(
            textwrap.dedent(
                """\
           while a:
               __version__ = 'a'
           """
            ),
            None,
        )

    def test_in_function(self):
        self.assert_version_equals(
            textwrap.dedent(
                """\
           __version__ = 'a'
           def f():
               __version__ = 'b'
           """
            ),
            "a",
        )
