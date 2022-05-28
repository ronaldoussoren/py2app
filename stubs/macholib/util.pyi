""" Minimal stubs """
import typing

NOT_SYSTEM_FILES: typing.List[str]

def in_system_path(filename: str) -> bool: ...
def is_platform_file(filename: str) -> bool: ...
