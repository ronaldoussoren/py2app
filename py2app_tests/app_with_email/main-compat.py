import sys


def function():
    import email.Encoders as enc  # noqa: F401
    from email import MIMEText  # noqa: F401


function()


def import_module(name):
    try:
        exec(f"import {name}")
        m = eval(name)
    except ImportError:
        print("* import failed")

    else:
        print(m.__name__)


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
