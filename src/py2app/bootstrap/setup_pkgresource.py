def _setup_pkgresources() -> None:
    import os
    import plistlib

    import pkg_resources  # noqa: I251

    resource_path = os.getenv("RESOURCEPATH")
    assert resource_path is not None
    with open(os.path.join(os.path.dirname(resource_path), "Info.plist"), "rb") as fp:

        pl = plistlib.load(fp)

    appname = pl.get("CFBundleIdentifier")
    if appname is None:
        appname = pl["CFBundleDisplayName"]
    path = os.path.expanduser(f"~/Library/Caches/{appname}/python-eggs")
    pkg_resources.set_extraction_path(path)


_setup_pkgresources()
