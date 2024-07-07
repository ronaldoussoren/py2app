CPU_TYPE_NAMES: dict[int, str]

LC_VERSION_MIN_MACOSX = 0x24


class build_version_command:
    platform: int
    minos: int
    sdk: int
    ntools: int


class version_min_command:
    version: int
    sdk: int


class dylib_command:
    name: int
    timestamp: int
    current_version: int
    compatibility_version: int
