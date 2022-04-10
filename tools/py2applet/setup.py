from distutils.core import setup

setup(
    app=["py2applet.py"],
    options={
        "py2app": {
            "excludes": ["py2app", "bdist_mpkg"],
            "argv_emulation": True,
            "semi_standalone": True,
            "site_packages": True,
        }
    },
)
