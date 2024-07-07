""" """

import typing

def lc_str_value(offset: int, cmd_info: tuple) -> bytes: ...

class MachO:
    headers: typing.List[typing.Any]  # XXX
    filename: str
    loader_path: str

    def __init__(self, filename: str, allow_unknown_load_commands: bool = False): ...
    def write(self, fileobj: typing.IO[bytes]) -> None: ...
    def rewriteLoadCommands(self, changefunc: typing.Callable[[str], str]) -> bool: ...
