import sys
if (sys.version_info[0] == 2 and sys.version_info[:2] >= (2,7)) or \
        (sys.version_info[0] == 3 and sys.version_info[:2] >= (3,2)):
    import unittest
else:
    import unittest2 as unittest

from py2app import filters

class Node (object):
    def __init__(self, filename):
        self.filename = filename

def return_true(value):
    return True

def return_false(value):
    return False


class FilterTest (unittest.TestCase):
    def test_not_stdlib_filter(self):
        prefix = '/system/python8.7'

        # Outside the tree:
        self.assertTrue(filters.not_stdlib_filter(
            Node('/foo/bar'), prefix))
        self.assertTrue(filters.not_stdlib_filter(
            Node(prefix+'rest'), prefix))

        # Site-specific directories within sys.prefix:
        self.assertTrue(filters.not_stdlib_filter(
            Node(prefix + '/lib/site-packages/foo.py'), prefix))
        self.assertTrue(filters.not_stdlib_filter(
            Node(prefix + '/lib/site-python/foo.py'), prefix))

        # Inside the tree:
        self.assertFalse(filters.not_stdlib_filter(
            Node(prefix + '/foo.py'), prefix))

    def test_not_system_filter(self):
        cur_func = filters.in_system_path
        try:
            filters.in_system_path = return_true
            self.assertFalse(filters.not_system_filter(Node('/tmp/foo')))

            filters.in_system_path = return_false
            self.assertTrue(filters.not_system_filter(Node('/tmp/foo')))
        finally:
            filters.in_system_path = cur_func

    def test_bundle_or_dylib_filter(self):
        node = Node('dummy.dylib')
        self.assertFalse(filters.bundle_or_dylib_filter(node))

        node.filetype = 'elf'
        self.assertFalse(filters.bundle_or_dylib_filter(node))

        node.filetype = 'bundle'
        self.assertTrue(filters.bundle_or_dylib_filter(node))

        node.filetype = 'dylib'
        self.assertTrue(filters.bundle_or_dylib_filter(node))

if __name__ == "__main__":
    unittest.main()
