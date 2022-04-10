from setuptools import setup

plist = {"NSPrincipleClass": "BasicPlugin"}

setup(
    name="BasicPlugin",
    plugin=["main.py"],
    options={
        "py2app": {
            "extension": ".bundle",
            "plist": plist,
        }
    },
)
