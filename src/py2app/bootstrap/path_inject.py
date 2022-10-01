def _path_inject(paths: "list[str]") -> None:
    import sys

    sys.path[:0] = paths
