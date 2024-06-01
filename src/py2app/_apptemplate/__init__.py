import importlib.resources
import subprocess
import sys
import sysconfig
from typing import List

from .._config import BuildArch

ARCH_FLAGS = {
    BuildArch.ARM64: ["-arch", "arm64"],
    BuildArch.X86_64: ["-arch", "x86_64"],
    BuildArch.UNIVERSAL2: ["-arch", "arm64", "-arch", "x86_64"],
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

    # Remove debug flags, those result in a dSYM directory for the build
    # and those aren't useful for us.
    while "-g" in flags:
        flags.remove("-g")

    return flags


def copy_app_launcher(
    path, *, arch: BuildArch, deployment_target: str, secondary: bool = False
) -> None:
    """
    Copy the app launcher template into the specified location
    """
    # XXX: Need to arrange for creating relevant launcher templates
    #      during wheel building
    # XXX: Maybe need to add the deployment target as well.
    # XXX: 'secondary' is not used yet.
    # XXX: Probably need to pass progress instance to warn when
    #      the launcher needs to be compiled.

    if secondary:
        source_fn = f"launcher-{arch}-{deployment_target}-{sys.abiflags}-secondary"
    else:
        source_fn = f"launcher-{arch}-{deployment_target}-{sys.abiflags}"

    launcher = importlib.resources.files(__name__).joinpath(source_fn)
    if launcher.exists():
        path.write_bytes(launcher.read_bytes())
        path.chmod(0o755)
        return

    launcher = importlib.resources.files(__name__).joinpath("launcher.m")
    subprocess.run(
        [
            "cc",
            "-o",
            path,
            launcher,
            "-rpath",
            "@executable_path/../../Frameworks",
            "-Wl,-headerpad_max_install_names",
            "-framework",
            "Foundation",
            f"-mmacosx-version-min={deployment_target}",
        ]
        + ARCH_FLAGS[arch]
        + _pyflags(),
        check=True,
    )


def get_app_plist(bundle_executable: str, plist: dict = {}) -> dict:  # noqa: B006, M511
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
        "NSPrincipalClass": "NSApplication",
    }
    pdict.update(plist)
    return pdict
