""" """

import collections
import typing

from macholib.MachOGraph import MachOGraph

class MachOStandalone:
    dest: str
    pending: collections.deque
    excludes: typing.List[str]
    mm: MachOGraph

    def __init__(
        self,
        base: str,
        dest: typing.Optional[str] = None,
        graph: typing.Optional[str] = None,
        env: typing.Optional[typing.Dict[str, str]] = None,
        executable_path: typing.Optional[str] = None,
    ): ...
    def run(self) -> typing.Set[str]: ...
