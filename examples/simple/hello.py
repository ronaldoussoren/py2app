import sys, os
import pprint

print(__file__)

__version__ = "1.0"


def somefunc():
    print("Hello from py2app")

    print("frozen: {}".format(repr(getattr(sys, "frozen", None))))

    import __main__

    print(__main__.__file__)
    print(f"sys.path: {sys.path}")
    print(f"sys.executable: {sys.executable}")
    print(f"sys.prefix: {sys.prefix}")
    print(f"sys.argv: {sys.argv}")
    print(f"os.getcwd(): {os.getcwd()}")
    pprint.pprint(dict(os.environ))
    import subprocess

    subprocess.call(["/usr/bin/say", "hello"])


if __name__ == "__main__":
    somefunc()
