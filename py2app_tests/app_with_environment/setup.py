from setuptools import setup

setup(
    name="BasicApp",
    app=["main.py"],
    options={
        "py2app": {
            "plist": {
                "LSEnvironment": {
                    "LANG": "nl_NL.latin1",
                    "LC_CTYPE": "nl_NL.UTF-8",
                    "EXTRA_VAR": "hello world",
                    "KNIGHT": "ni!",
                }
            }
        }
    },
)
