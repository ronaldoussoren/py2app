def _chdir_resource() -> None:
    import os

    os.chdir(os.environ["RESOURCEPATH"])


_chdir_resource()
