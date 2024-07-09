"""
Helpers for auditing the result
of "MachoStandalone" for issues
that might affect portability.
"""

import os
import pathlib
import typing

from macholib import MachO, mach_o
from macholib.util import is_platform_file


def decode_deployment_target(value: int) -> str:
    """
    Return a user friendly representation of an encoded deployment target
    """
    micro = value & 0xFF
    minor = value >> 8 & 0xFF
    macro = value >> 16 & 0xFF
    if micro == 0:
        if minor == 0:
            return f"{macro}"
        return f"{macro}.{minor}"
    return f"{macro}.{minor}.{micro}"


def macho_files(base: pathlib.Path) -> typing.Iterator[pathlib.Path]:
    """
    Yield Path objects for all MachO files in the filesystem
    tree starting at *base*.
    """
    for root, _, files in os.walk(str(base.resolve())):
        for fn in files:
            p = pathlib.Path(root) / fn
            if p.is_symlink():
                continue
            try:
                if is_platform_file(str(p)):
                    yield p
            except PermissionError:
                continue


def audit_macho_issues(
    bundle_path: pathlib.Path,
) -> typing.Tuple[typing.Optional[str], typing.Optional[str], typing.List[str]]:
    """
    Returns (architecture, deployment_target, warnings)

    * ``architecture`` is the the common architecture(set) for files in the bundle
       (``univeral2``, ``x86_64`` or ``arm64``), and is None when there are two
       single-architecture files for different architectures.

    * ``deployment_target`` is the most recent deployment target supported by all
      files in the bundle bundle (for example "13.2")

    * The ``warnings`` are a list of warnings to be shown to the user.
    """
    # XXX: Adjust for py2app's needs:
    # - Check if linked to libraries actually exist:
    #   1. @rpath/... should be present in Frameworks folder
    #   2. system paths should be in FS or in dyld "cache"

    # Deployment target per CPU type, this allows us to report more clearly
    # about issues.
    warnings = []
    deployment_targets = {
        "arm64": 0xB0000,
        "x86_64": 0xA0900,
    }
    architecture: typing.Optional[str] = "universal2"

    # Default @rpath for stub executables:
    base_rpath = {bundle_path / "Frameworks"}

    for macho_path in macho_files(bundle_path):
        m = MachO.MachO(str(macho_path))
        cur_archs = set()
        for hdr in m.headers:
            hdr_arch = mach_o.CPU_TYPE_NAMES[hdr.header.cputype].lower()
            if hdr_arch not in {"x86_64", "arm64"}:
                continue
            cur_archs.add(hdr_arch)

            # Look for a version command to check the deployment target.
            for cmd in hdr.commands:
                if isinstance(cmd[1], mach_o.build_version_command):
                    deployment_targets[hdr_arch] = max(
                        cmd[1].minos, deployment_targets[hdr_arch]
                    )
                    break

                elif isinstance(cmd[1], mach_o.version_min_command):
                    deployment_targets[hdr_arch] = max(
                        cmd[1].version, deployment_targets[hdr_arch]
                    )
                    break
            else:
                # The header does not have a load command with
                # a deployment version.
                #
                # That's generally harmless, but do warn about this.
                warnings.append(f"no deployment target in {macho_path}")

            # Check that all link commands refer to either a system location
            # or start with '@' (@rpath, @executable_path, ...)

            # Calculate the RPATH search path for the current file.
            rpath = set(base_rpath)
            for cmd in hdr.commands:
                if isinstance(cmd[1], mach_o.rpath_command):
                    rpath.add(
                        pathlib.Path(MachO.lc_str_value(cmd[1].path, cmd).decode())
                    )

            # Validate commands that load a shared library or framework
            for cmd in hdr.commands:
                if isinstance(cmd[1], mach_o.dylib_command):
                    name = MachO.lc_str_value(cmd[1].name, cmd).decode()
                    if (
                        not name.startswith("/usr/lib")
                        and not name.startswith("/System/Library/Frameworks")
                        and not name.startswith("@")
                    ):
                        warnings.append(
                            f"{str(macho_path)!r} links to library {name!r} outside of system locations"
                        )
                    elif name.startswith("@loader_path/"):
                        _, _, relpath = name.partition("/")

                        if not (macho_path.parent / relpath).exists():
                            warnings.append(
                                f"{str(macho_path)!r} links to library {name!r} that "
                                f"doesn't exist at {str(macho_path.parent / relpath)!r}"
                            )

                    elif name.startswith("@rpath/"):
                        _, _, relpath = name.partition("/")

                        for rp in rpath:
                            if (rp / relpath).exists():
                                break
                        else:
                            warnings.append(
                                f"{str(macho_path)!r} links to library {name!r} that "
                                f"doesn't exist on rpath: {', '.join(map(str, sorted(rpath)))}"
                            )

                    elif name.startswith("@executable_path/"):
                        # These shouldn't be present in practice as that would
                        # break when using virtual environments.

                        dirpath = bundle_path / "Contents/MacOS"
                        _, _, relpath = name.partition("/")
                        if not os.path.exists(dirpath / relpath):
                            warnings.append(
                                f"{str(macho_path)!r} uses {name!r} to link to non-existing {str(dirpath / relpath)!r}"
                            )

                    elif name.startswith("@"):
                        warnings.append(
                            f"{str(macho_path)!r}: Unhandled special path in link command: {name}"
                        )

        if "x86_64" in cur_archs and "arm64" in cur_archs:
            continue
        elif "x86_64" in cur_archs:
            if architecture in {"universal2", "x86_64"}:
                architecture = "x86_64"
            else:
                architecture = None
        elif "arm64" in cur_archs:
            if architecture in {"universal2", "arm64"}:
                architecture = "arm64"
            else:
                architecture = None

    if architecture == "universal2":
        deployment_target = min(deployment_targets.values())
        if deployment_target < 0xB0000:
            if deployment_targets["arm64"] > 0xB0000:
                warnings.append(
                    "Deployment target less than 11.0, but arm64 targets "
                    f"{decode_deployment_target(deployment_targets['arm64'])})"
                )

    elif architecture is None:
        deployment_target = None

    else:
        deployment_target = deployment_targets[architecture]

    return (
        architecture,
        (
            decode_deployment_target(deployment_target)
            if deployment_target is not None
            else None
        ),
        sorted(set(warnings)),  # Deduplicate
    )
