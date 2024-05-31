import importlib.resources
import subprocess
import sys
import sysconfig

from .._config import BuildArch

ARCH_FLAGS = {
    BuildArch.ARM64: ["-arch", "arm64"],
    BuildArch.X86_64: ["-arch", "x86_64"],
    BuildArch.UNIVERSAL2: ["-arch", "arm64", "-arch", "x86_64"],
}


def pyflags():
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

    print(" ".join(flags))
    return flags


def copy_app_launcher(path, *, arch: BuildArch, secondary: bool = False) -> None:
    """
    Copy the app launcher template into the specified location
    """
    # XXX: For now the template gets compiled every time, need to find
    #      a way to build these executables when generating the wheel.
    # XXX: Maybe need to add the deployment target as well.
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
        ]
        + ARCH_FLAGS[arch]
        + pyflags(),
        check=True,
    )


def get_app_plist(bundle_executable: str, plist: dict = {}) -> dict:  # noqa: B006, M511
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
