import sys

def function():
    import quot
    import quot.queue

def import_module(name):
    try:
        exec("import %s"%(name,))
        m = eval(name)
    except ImportError as exc:
        print("* import failed: %s path: %s"%(exc, sys.path))

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
            exec (line)
        except SystemExit:
            raise

        except Exception:
            print("* Exception " + str(sys.exc_info()[1]))

        sys.stdout.flush()
        sys.stderr.flush()
