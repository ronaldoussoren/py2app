import typing

from .MachO import MachO

class MachOGraph:
    env: typing.Optional[typing.Dict[str, str]]
    executable_path: typing.Optional[str]

    def __init__(
        self,
        debug: int = 0,
        graph: None = None,
        env: typing.Optional[typing.Dict[str, str]] = None,
        executable_path: typing.Optional[str] = None,
    ) -> None: ...
    def locate(
        self, filename: str, loader: typing.Optional[str] = None
    ) -> typing.Optional[str]: ...
    def findNode(
        self, name: str, loader: typing.Optional[str] = None
    ) -> typing.Optional[MachO]: ...
    def run_file(self, pathname: str, caller: typing.Optional[str] = None) -> MachO: ...
    def load_file(
        self, name: str, loader: typing.Optional[str] = None
    ) -> typing.Optional[MachO]: ...
    def scan_node(self, node: MachO) -> None: ...
    def graphreport(self, fileobj: typing.Optional[typing.IO[str]] = None) -> None: ...
