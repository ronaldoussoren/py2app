""" """

import typing

def imp_find_module(
    name: str, path: typing.Sequence[str] | str | None = None
) -> typing.Tuple[typing.IO | None, str, str]: ...
