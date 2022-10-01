def _disable_linecache() -> None:
    import linecache

    def fake_getline(
        filename: str, lineno: int, module_globals: "dict|None" = None
    ) -> str:
        return ""

    linecache.orig_getline = linecache.getline  # type: ignore
    linecache.getline = fake_getline


_disable_linecache()
