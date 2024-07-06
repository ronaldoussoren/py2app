def _disable_linecache() -> None:
    import linecache

    def fake_getline(
        filename: str, lineno: int, module_globals: "dict|None" = None
    ) -> str:
        return ""

    def fake_getlines(filename: str, module_globals: "dict|None" = None) -> "list[str]":
        return []

    def fake_checkcache(filename: "str|None" = None) -> None:
        return

    def fake_updatecache(
        filename: str, module_globals: "dict|None" = None
    ) -> "list[str]":
        return []

    linecache.orig_getline = linecache.getline  # type: ignore
    linecache.getline = fake_getline

    linecache.orig_getlines = linecache.getlines  # type: ignore
    linecache.getlines = fake_getlines

    linecache.orig_checkcache = linecache.checkcache  # type: ignore
    linecache.checkcache = fake_checkcache

    linecache.orig_updatecache = linecache.updatecache  # type: ignore
    linecache.updatecache = fake_updatecache


_disable_linecache()
