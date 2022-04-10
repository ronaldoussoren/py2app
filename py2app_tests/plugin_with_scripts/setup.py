from setuptools import setup

plist = {"NSPrincipleClass": "BasicPlugin"}

setup(
    name="BasicPlugin",
    plugin=["main.py"],
    options={
        "py2app": {
            "extra_scripts": ["helper1.py", "helper2.py"],
            "extension": ".bundle",
            "plist": plist,
        }
    },
)
