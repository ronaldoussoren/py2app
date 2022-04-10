from setuptools import setup

setup(
    name="BasicApp",
    app=["main.py"],
    options={
        "py2app": {
            "emulate_shell_environment": True,
        }
    },
)
