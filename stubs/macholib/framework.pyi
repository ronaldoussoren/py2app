import typing

class _FrameworkInfo(typing.TypedDict):
    location: str
    name: str
    shortname: str
    version: str
    suffix: str

def framework_info(filename: str) -> typing.Optional[_FrameworkInfo]: ...
