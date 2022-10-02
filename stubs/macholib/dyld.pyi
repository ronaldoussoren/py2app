""" """

__all__ = ("framework_info", "dyld_find", "framework_find")

from macholib.framework import framework_info

def dyld_find(
    name: str,
    executable_path: str | None = None,
    env: dict[str, str] | None = None,
    loader_path: str | None = None,
) -> str: ...
def framework_find(
    fn: str, executable_path: str | None = None, env: dict[str, str] | None = None
) -> str: ...
