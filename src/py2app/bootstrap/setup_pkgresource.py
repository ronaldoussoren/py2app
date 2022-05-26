def _setup_pkgresources():
    import os
    import plistlib

    import pkg_resources  # noqa: I251

    with open(
        os.path.join(os.path.dirname(os.getenv("RESOURCEPATH")), "Info.plist"), "rb"
    ) as fp:

        pl = plistlib.load(fp)

    appname = pl.get("CFBundleIdentifier")
    if appname is None:
        appname = pl["CFBundleDisplayName"]
    path = os.path.expanduser(f"~/Library/Caches/{appname}/python-eggs")
    pkg_resources.set_extraction_path(path)


_setup_pkgresources()
