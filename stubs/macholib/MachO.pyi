""" """

import typing

class MachO:
    headers: typing.List[typing.Any]  # XXX
    filename: str
    loader_path: str

    def __init__(self, filename: str, allow_unknown_load_commands: bool = False): ...
