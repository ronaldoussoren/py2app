import pathlib
import sys

from .._config import BuildArch
from . import LauncherType, copy_app_launcher


def _deployment_targets():
    """
    Yield all deployment targets support by the current python build
    """
    # XXX: Consider changing the target after building the bundle,
    #      and generate only two sets of binaries (10.9, 11)
    import sysconfig

    deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
    assert deployment_target is not None
    min_target = list(map(int, deployment_target.split(".")))

    # XXX: For now the deployment target of python itself is
    #      good enough
    yield deployment_target
    return

    if min_target[0] == 10:
        for i in range(min_target[1], 16):
            yield f"10.{i}"

        for i in range(11, 16):
            yield f"{i}"

    else:
        for i in range(min_target[0], 16):
            yield f"{i}"


def build_executable_cache():
    """
    Build the cached executables for the current python release
    """

    for program_type in LauncherType:
        for deployment_target in _deployment_targets():
            for arch in BuildArch:
                fn = (
                    pathlib.Path(__file__).parent
                    / f"launcher-{arch.value}-{deployment_target}-{sys.abiflags}-{program_type.value}"
                )
                fn.unlink(missing_ok=True)
                print(f"Generate {fn.name}")
                copy_app_launcher(
                    fn,
                    arch=arch,
                    deployment_target=deployment_target,
                    program_type=program_type,
                )


if __name__ == "__main__":
    build_executable_cache()
