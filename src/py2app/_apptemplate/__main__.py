import pathlib
import sys
import sysconfig

from .._config import BuildArch
from . import LauncherType, copy_app_launcher


def build_executable_cache() -> None:
    """
    Build the cached executables for the current python release
    """

    for program_type in LauncherType:
        deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
        assert deployment_target is not None

        for arch in BuildArch:
            fn = (
                pathlib.Path(__file__).parent
                / f"launcher-{arch.value}-{sys.abiflags}-{program_type.value}"
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
