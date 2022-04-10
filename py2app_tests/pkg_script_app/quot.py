import sys


def function():
    import quot  # noqa: F401
    import quot.queue  # noqa: F401


def import_module(name):
    try:
        exec(f"import {name}")
        m = eval(name)
    except ImportError as exc:
        print(f"* import failed: {exc} path: {sys.path}")

    else:
        print(m.__name__)


def print_path():
    print(sys.path)


if __name__ == "__main__":
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
