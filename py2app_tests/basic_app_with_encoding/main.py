"""
- coding: utf-8 -
This is a script with a non-ASCII encoding

German for Lion is Löwe.
"""

import sys


def function():
    import decimal  # noqa: F401


def import_module(name):
    try:
        exec(f"import {name}")
        m = eval(name)
    except ImportError:
        print("* import failed")

    else:
        # for k in name.split('.')[1:]:
        #    m = getattr(m, k)
        print(m.__name__)


def print_path():
    print(sys.path)


while True:
    line = sys.stdin.readline()
    if not line:
        break

    try:
        exec(line)
    except SystemExit:
        raise

    except Exception:
        print("* Exception " + str(sys.exc_info()[1]))

    sys.stdout.flush()
    sys.stderr.flush()
