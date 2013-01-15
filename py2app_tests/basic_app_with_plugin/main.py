import sys


def function():
    import decimal

def import_module(name):
    try:
        exec ("import %s"%(name,))
        m = eval(name)
    except ImportError:
        print ("* import failed")

    else:
        #for k in name.split('.')[1:]:
        #    m = getattr(m, k)
        print (m.__name__)

def print_path():
    print(sys.path)

while True:
    line = sys.stdin.readline()
    if not line:
        break

    try:
        exec (line)
    except SystemExit:
        raise

    except Exception:
        print ("* Exception " + str(sys.exc_info()[1]))

    sys.stdout.flush()
    sys.stderr.flush()
