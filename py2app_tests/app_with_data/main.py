import sys


def function():
    import decimal

def _fetch_path(gl, name):
    parts = name.split('.')
    gl = gl[parts[0]]

    for n in parts[1:]:
        gl = getattr(gl, n)
    return gl

def import_module(name):
    try:
        gl = {}
        exec ("import %s"%(name,), gl, gl)
        m = _fetch_path(gl, name)
    except ImportError:
        print ("* import failed")

    else:
        for k in name.split('.')[1:]:
            m = getattr(m, k)
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
