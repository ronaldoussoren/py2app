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


def decode_deployment_target(value):
    micro = value & 0xFF
    minor = value >> 8 & 0xFF
    macro = value >> 16 & 0xFF
    return f"{macro}.{minor}.{micro}"


def macho_files(base: pathlib.Path) -> typing.Iterator[pathlib.Path]:
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
) -> typing.Tuple[str, str, typing.List[str]]:
    """
    Returns (architecture, deployment_target, warnings)

    * ``architecture`` is the the common architecture(set) for files in the bundle
       (``univeral2``, ``x86_64`` or ``arm64``), and is None when there are two
       single-architecture files for different architectures.

    * ``deployment_target`` is the most recent deployment target for files in the
      bunlde (for example "13.2")

    * The ``warnings`` are a list of warnings to be shown to the user.
    """

    # Deployment target per CPU type, this allows us to report more clearly
    # about issues.
    warnings = []
    deployment_targets = {
        "arm64": 0xB0000,
        "x86_64": 0xA0900,
    }
    architecture = "universal2"

    for macho_path in macho_files(bundle_path):
        m = MachO.MachO(str(macho_path))
        cur_archs = set()
        for hdr in m.headers:
            hdr_arch = mach_o.CPU_TYPE_NAMES[hdr.header.cputype].lower()
            if hdr_arch not in {"x86_64", "arm64"}:
                continue
            cur_archs.add(hdr_arch)

            for cmd in hdr.commands:
                if isinstance(cmd[1], mach_o.build_version_command):
                    deployment_targets[hdr_arch] = cmd[1].minos
                    break

                elif isinstance(cmd[1], mach_o.version_min_command):
                    deployment_targets[hdr_arch] = cmd[1].version
                    break
            else:
                # The header does not have a load command with
                # a deployment version.
                #
                # That's generally harmless, but do warn about this.
                warnings.append(f"no deployment target in {macho_path}")

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
        warnings,
    )


if __name__ == "__main__":
    for p in pathlib.Path("/Applications").iterdir():
        if not p.is_dir():
            continue

        architecture, deployment_target, warnings = audit_macho_issues(p)
        print(f"{p!s}:")
        print(f"  Common architecture: {architecture}")
        print(f"  Deployment target:   {deployment_target}")
        for w in warnings:
            print(w)
        print()
