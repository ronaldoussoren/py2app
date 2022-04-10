import os
import re
import unittest


class TestRecipeImports(unittest.TestCase):
    def test_imports(self):
        import py2app.recipes as m

        dirname = os.path.dirname(m.__file__)

        all_imported = set()
        for fn in os.listdir(dirname):
            if fn.startswith("__"):
                continue
            if fn.endswith(".py"):
                with open(os.path.join(dirname, fn)) as fp:
                    for ln in fp:
                        m = re.search(r"^\s*import (.*)", ln)
                        if m is not None:
                            for nm in m.group(1).split(","):
                                all_imported.add(nm.strip())

        for fn in os.listdir(dirname):
            if fn.startswith("__"):
                continue

            mod = os.path.splitext(fn)[0]
            if mod not in all_imported:
                continue

            try:
                m = __import__(mod)
            except ImportError:
                pass

            else:

                self.fail(f"Can import {mod!r}")
