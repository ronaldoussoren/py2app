""" """
import typing
import collections

class MachOStandalone:
    dest: str
    pending: collections.deque

    def __init__(
        self,
        base: str,
        dest: typing.Optional[str] = None,
        graph: typing.Optional[str] = None,
        env: typing.Dict[str, str] = None,
        executable_path: typing.Optional[str] = None,
    ): ...
