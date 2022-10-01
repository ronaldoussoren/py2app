import textwrap
import typing
from io import StringIO

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("multiprocessing")
    if m is None:
        return None

    # This is a fairly crude hack to get multiprocessing to do the
    # right thing without user visible changes in py2app.
    # In particular: multiprocessing assumes that a special command-line
    # should be used when "sys.frozen" is set. That is not necessary
    # with py2app even though it does set "sys.frozen".
    prescript = textwrap.dedent(
        """\
        def _boot_multiprocessing():
            import sys
            import multiprocessing.spawn

            orig_get_command_line = multiprocessing.spawn.get_command_line
            def wrapped_get_command_line(**kwargs):
                orig_frozen = sys.frozen
                del sys.frozen
                try:
                    return orig_get_command_line(**kwargs)
                finally:
                    sys.frozen = orig_frozen
            multiprocessing.spawn.get_command_line = wrapped_get_command_line

        _boot_multiprocessing()
        """
    )

    return {"prescripts": [StringIO(prescript)]}
