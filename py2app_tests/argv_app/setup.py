from setuptools import setup

setup(
    name="BasicApp",
    app=["main.py"],
    options={
        "py2app": {
            "argv_emulation": True,
        }
    },
)
