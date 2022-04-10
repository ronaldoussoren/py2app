def _setup_pkgresources():
    import os
    import plistlib

    import pkg_resources

    if hasattr(plistlib, "load"):
        with open(
            os.path.join(os.path.dirname(os.getenv("RESOURCEPATH")), "Info.plist"), "rb"
        ) as fp:

            pl = plistlib.load(fp)

    else:
        # 2.7
        pl = plistlib.readPlist(
            os.path.join(os.path.dirname(os.getenv("RESOURCEPATH")), "Info.plist")
        )

    appname = pl.get("CFBundleIdentifier")
    if appname is None:
        appname = pl["CFBundleDisplayName"]
    path = os.path.expanduser(f"~/Library/Caches/{appname}/python-eggs")
    pkg_resources.set_extraction_path(path)


_setup_pkgresources()
