import enum
import importlib.resources
import pathlib
import subprocess
import sys
import sysconfig
from typing import List

from .._config import BuildArch


class LauncherType(enum.Enum):
    STUB_APP = "app"
    STUB_PLUGIN = "plugin"
    PYTHON_BINARY = "python"


ARCH_FLAGS = {
    BuildArch.ARM64: ["-arch", "arm64"],
    BuildArch.X86_64: ["-arch", "x86_64"],
    BuildArch.UNIVERSAL2: ["-arch", "arm64", "-arch", "x86_64"],
}

LAUNCHER_FLAGS = {
    LauncherType.STUB_APP: [],
    LauncherType.STUB_PLUGIN: ["-DBUNDLE_PLUGIN", "-bundle"],
    LauncherType.PYTHON_BINARY: ["-DLAUNCH_PYTHON"],
}


def _pyflags() -> List[str]:
    """
    Return compiler flags to be used to compile for the current python
    version/build.
    """
    flags = [
        "-I" + sysconfig.get_path("include"),
        "-I" + sysconfig.get_path("platinclude"),
    ]
    flags.extend(sysconfig.get_config_var("CFLAGS").split())
    flags.append("-L" + sysconfig.get_config_var("LIBPL"))
    flags.append("-lpython" + sysconfig.get_config_var("VERSION") + sys.abiflags)
    flags.extend(
        sysconfig.get_config_var("LIBS").split()
        + sysconfig.get_config_var("SYSLIBS").split()
    )

    # drop '-arch' flags from _pyflags, those will be added later
    for idx in range(len(flags) - 1, -1, -1):
        if flags[idx] == "-arch":
            del flags[idx : idx + 2]

    # Remove debug flags, those result in a dSYM directory for the build
    # and those aren't useful for us.
    while "-g" in flags:
        flags.remove("-g")

    return flags


def copy_launcher(
    path: pathlib.Path,
    *,
    arch: BuildArch,
    program_type: LauncherType = LauncherType.STUB_APP,
    deployment_target: str,
    debug_macho_usage: bool = False,
) -> None:
    """
    Copy the app launcher template into the specified location
    """

    # The deployment target is not used as part of the cache file name
    # because the target version will be replaced while building a bundle.
    source_fn = f"launcher-{arch.value}-{sys.abiflags}-{program_type.value}"
    launcher = importlib.resources.files(__name__).joinpath(source_fn)
    if debug_macho_usage:
        # The Traversable ABC does not have an 'exists' method, just
        # try to access the file and handle the exception when the file
        # does not exist.
        try:
            data = launcher.read_bytes()
        except OSError:
            pass

        else:
            path.write_bytes(data)
            path.chmod(0o755)
            return

    launcher = importlib.resources.files(__name__).joinpath("launcher.m")

    subprocess.run(
        (
            [
                "cc",
                "-o",
                str(path),
                str(launcher),
                "-rpath",
                "@loader_path/../Frameworks",
                "-Wl,-headerpad_max_install_names",
                "-framework",
                "Foundation",
                f"-mmacosx-version-min={deployment_target}",
            ]
            + LAUNCHER_FLAGS[program_type]
            + ARCH_FLAGS[arch]
            + _pyflags()
            + (["-DENABLE_MACHO_DEBUG"] if debug_macho_usage else [])
        ),
        check=True,
    )


def get_plist(
    bundle_executable: str,
    plist: dict = {},  # noqa: B006, M511
    is_plugin: bool = False,
) -> dict:
    """
    Return a plist template for an app bundle, merging 'plist' into the
    default values.
    """
    # XXX: Need to audit the default plist
    pdict = {
        "CFBundleDevelopmentRegion": "English",
        "CFBundleDisplayName": plist.get("CFBundleName", bundle_executable),
        "CFBundleExecutable": bundle_executable,
        "CFBundleIconFile": bundle_executable,
        "CFBundleIdentifier": f"{''.join(bundle_executable.split())}",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": bundle_executable,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": plist.get("CFBundleVersion", "0.0"),
        "CFBundleSignature": "????",
        "CFBundleVersion": "0.0",
        "LSHasLocalizedDisplayName": False,
        "NSAppleScriptEnabled": False,
        "NSHumanReadableCopyright": "Copyright not specified",
        "NSMainNibFile": "MainMenu",
        "NSPrincipalClass": bundle_executable if is_plugin else "NSApplication",
    }
    pdict.update(plist)
    return pdict
